"""
One-command Qwen3-VL-4B-Instruct MMMU validation evaluation.

Pipeline:
    HF MMMU validation (30 subject configs, pinned revision)
        -> official-style MMMU prompt
        -> Qwen3-VL inference with vLLM (official Instruct sampling recipe)
        -> deterministic MMMU-style parser
        -> gold/prediction result records (+ generation diagnostics)
        -> subject accuracy + Overall macro average

This intentionally does NOT use Qwen's MMMU evaluation judge model.
It also does NOT use MMMU_DEV_VAL.tsv.

Model:
    Qwen/Qwen3-VL-4B-Instruct
    revision:
    ebb281ec70b05090aa6165b016eac8ec08e71b17

Dataset:
    MMMU/MMMU
    revision:
    98e6ac0cb9b7b2cd2c991b85a50762edc4aedc68

Defaults follow the "Evaluation Reproduction -> Generation Hyperparameters
-> Instruct models" block of the official Qwen3-VL README
(https://github.com/QwenLM/Qwen3-VL#evaluation-reproduction):

    greedy=false seed=3407 top_p=0.8 top_k=20 temperature=0.7
    repetition_penalty=1.0 presence_penalty=1.5 out_seq_length=32768

Image resolution defaults to the pinned checkpoint's own processor config
(`processor.image_processor.size`, i.e. the model-card default) unless
--min_pixels/--max_pixels are given explicitly.

Outputs (with --run_dir RUN):
    RUN/predictions.jsonl         one record per sample (prompt, raw output,
                                  parsed answer, tokens, logprob summary,
                                  image sizes, timing, gold explanation ...)
    RUN/per_subject/<Subject>.jsonl   checkpoint per subject (enables --resume)
    RUN/metrics.json              subject accuracies, Overall, timing, env
    RUN/manifest.json             git sha, args, resolved settings, versions,
                                  GPU info, exact prompt example
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from tqdm import tqdm
from transformers import AutoProcessor
from vllm import LLM, SamplingParams

from dataset import DATASET_NAME, DATASET_REVISION, SUBJECTS, load_mmmu_validation
from evaluator import evaluate, is_correct
from parser import parse_answer
import prompt as prompt_mod
from prompt import MAX_PIXELS, MIN_PIXELS, PROMPT_VARIANTS, build_messages, build_vllm_input, parse_options


MODEL_NAME = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"

# Qwen3-VL: 16px patch x 2 spatial merge -> one visual token per 32x32 block.
VISUAL_TOKEN_SIDE = 32

# Official Qwen3-VL Instruct recipe (see module docstring).
OFFICIAL_RECIPE = {
    "greedy": False,
    "seed": 3407,
    "top_p": 0.8,
    "top_k": 20,
    "temperature": 0.7,
    "repetition_penalty": 1.0,
    "presence_penalty": 1.5,
    "out_seq_length": 32768,
}


class VRAMPoller:
    """Background thread that polls nvidia-smi and tracks peak GPU
    memory usage across all visible GPUs. Needed because vLLM's V1
    engine runs model load + inference in a separate EngineCore
    subprocess, so torch.cuda.max_memory_allocated() in the main
    process always reads ~0."""

    def __init__(self, interval_sec: float = 0.5):
        self.interval_sec = interval_sec
        self.peak_gb = 0.0
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def _query_used_mib(self) -> float:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True,
        )
        return sum(int(x) for x in result.stdout.strip().split("\n"))

    def _poll(self) -> None:
        while not self._stop_event.is_set():
            try:
                used_gb = self._query_used_mib() / 1024
                if used_gb > self.peak_gb:
                    self.peak_gb = used_gb
            except Exception:
                pass
            time.sleep(self.interval_sec)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> float:
        self._stop_event.set()
        self._thread.join(timeout=2.0)
        if self.peak_gb == 0.0:
            print("  WARNING: VRAM poller never got a successful nvidia-smi reading.")
        return self.peak_gb


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _pixels_arg(value: str) -> Any:
    """'auto' -> use the checkpoint processor default; else int (bash-style
    expressions like 256*32*32 are accepted)."""
    value = str(value).strip().lower()
    if value == "auto":
        return "auto"
    if "*" in value:
        out = 1
        for part in value.split("*"):
            out *= int(part)
        return out
    return int(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the complete MMMU validation baseline in one command."
    )

    parser.add_argument("--model_path", type=str, required=True,
                        help="HF model id or local model directory.")
    parser.add_argument("--data_root", type=str, required=True,
                        help="Local Hugging Face cache directory for MMMU.")

    # Output layout. --run_dir is the recommended way; the two file
    # arguments are kept for backward compatibility with older scripts.
    parser.add_argument("--run_dir", type=str, default=None,
                        help="Directory for predictions/metrics/manifest/"
                             "per-subject checkpoints.")
    parser.add_argument("--output_file", type=str, default=None,
                        help="JSONL prediction/result file "
                             "(default: <run_dir>/predictions.jsonl or "
                             "results/mmmu_predictions.jsonl).")
    parser.add_argument("--metrics_file", type=str, default=None,
                        help="JSON metrics output file "
                             "(default: <run_dir>/metrics.json or "
                             "results/mmmu_metrics.json).")
    parser.add_argument("--resume", action="store_true", default=False,
                        help="Skip subjects whose per-subject checkpoint in "
                             "<run_dir>/per_subject is complete.")

    # Generation recipe (defaults = official Qwen3-VL Instruct recipe).
    parser.add_argument(
        "--greedy", action="store_true", default=False,
        help="Greedy decoding (temperature=0). The official recipe sets "
             "greedy='false'; this exists only for ablation.")
    parser.add_argument("--seed", type=int, default=OFFICIAL_RECIPE["seed"])
    parser.add_argument("--temperature", type=float,
                        default=OFFICIAL_RECIPE["temperature"])
    parser.add_argument("--top_p", type=float, default=OFFICIAL_RECIPE["top_p"])
    parser.add_argument("--top_k", type=int, default=OFFICIAL_RECIPE["top_k"])
    parser.add_argument("--repetition_penalty", type=float,
                        default=OFFICIAL_RECIPE["repetition_penalty"])
    parser.add_argument("--presence_penalty", type=float,
                        default=OFFICIAL_RECIPE["presence_penalty"])
    parser.add_argument("--max_new_tokens", type=int,
                        default=OFFICIAL_RECIPE["out_seq_length"],
                        help="= out_seq_length in the official recipe.")

    # Visual token budget. 'auto' = processor default of the pinned
    # checkpoint (model-card setting). Ints or 256*32*32 style allowed.
    parser.add_argument("--min_pixels", type=_pixels_arg, default="auto")
    parser.add_argument("--max_pixels", type=_pixels_arg, default="auto")

    # vLLM / context settings.
    parser.add_argument("--max_model_len", type=int, default=32768)
    parser.add_argument("--gpu_memory_utilization", type=float, default=0.90)
    parser.add_argument("--tensor_parallel_size", type=int, default=None,
                        help="Defaults to the number of visible CUDA devices.")
    parser.add_argument("--max_num_seqs", type=int, default=None,
                        help="vLLM max concurrent sequences (default: vLLM's).")

    # Diagnostics.
    parser.add_argument(
        "--batch_mode", choices=["subject", "all"], default="subject",
        help="'subject': one vLLM generate() call per subject (gives "
             "per-subject wall time + checkpoint/resume; slightly less "
             "batching efficiency). 'all': single call over every sample.")
    parser.add_argument(
        "--logprobs", type=int, default=0,
        help="If >0, request top-N logprobs per generated token and store "
             "a per-sample summary (cumulative/mean logprob, first-token "
             "top-N). Per-token lists are NOT stored.")
    parser.add_argument(
        "--no_prompt_text", action="store_true", default=False,
        help="Do not store the full chat-templated prompt per sample.")

    # Optional debugging only. Normal assignment run must leave this unset.
    parser.add_argument("--max_samples", type=int, default=None,
                        help="Debug only: evaluate only the first N samples.")
    parser.add_argument("--subjects", type=str, default=None,
                        help="Debug only: comma-separated subject subset.")

    # Ablations (anything other than the defaults is NOT the baseline).
    parser.add_argument("--prompt_variant", choices=sorted(PROMPT_VARIANTS),
                        default="official",
                        help="Instruction wording (see code/prompt.py). "
                             "'official' = baseline.")
    parser.add_argument("--img_types", type=str, default=None,
                        help="Keep only samples whose MMMU img_type contains one "
                             "of these (comma-separated), e.g. 'Sheet Music,"
                             "Chemical Structures'.")
    parser.add_argument("--no_images", action="store_true", default=False,
                        help="Text-only ablation: replace images with '[image]'.")
    parser.add_argument("--question_types", type=str, default=None,
                        help="Comma-separated subset of question types, e.g. "
                             "'open'. Default: all.")

    return parser.parse_args()


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _run_cmd(cmd: List[str]) -> Optional[str]:
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              check=True, timeout=30).stdout.strip()
    except Exception:
        return None


def _pkg_version(name: str) -> Optional[str]:
    try:
        import importlib.metadata as md
        return md.version(name)
    except Exception:
        return None


def collect_environment() -> Dict[str, Any]:
    """Everything needed to reproduce / compare this run later."""
    env: Dict[str, Any] = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "git_commit": _run_cmd(["git", "rev-parse", "HEAD"]),
        "git_branch": _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "git_dirty": bool(_run_cmd(["git", "status", "--porcelain"]) or ""),
        "packages": {
            name: _pkg_version(name)
            for name in ["vllm", "torch", "transformers", "qwen-vl-utils",
                         "datasets", "flashinfer-python", "huggingface-hub",
                         "tokenizers", "pillow"]
        },
        "torch_cuda": getattr(torch.version, "cuda", None),
        "cudnn": (torch.backends.cudnn.version()
                  if torch.backends.cudnn.is_available() else None),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "gpus": [],
        "env_vars": {
            k: os.environ.get(k)
            for k in ["HF_HOME", "HF_HUB_OFFLINE", "VLLM_WORKER_MULTIPROC_METHOD",
                      "VLLM_ATTENTION_BACKEND", "PYTORCH_CUDA_ALLOC_CONF",
                      "OMP_NUM_THREADS"]
            if os.environ.get(k) is not None
        },
    }
    smi = _run_cmd(["nvidia-smi",
                    "--query-gpu=index,name,driver_version,memory.total",
                    "--format=csv,noheader,nounits"])
    if smi:
        for line in smi.splitlines():
            idx, name, drv, mem = [x.strip() for x in line.split(",")]
            env["gpus"].append({"index": int(idx), "name": name,
                                "driver": drv, "memory_total_mib": int(mem)})
    try:
        for i in range(torch.cuda.device_count()):
            env.setdefault("torch_devices", []).append(
                torch.cuda.get_device_name(i))
    except Exception:
        pass
    return env


def resolve_pixels(arg: Any, processor: Any, key: str, fallback: int) -> Dict[str, Any]:
    """Resolve 'auto' to the checkpoint's processor default (fails loudly)."""
    if arg != "auto":
        return {"value": int(arg), "source": "cli"}
    size = getattr(getattr(processor, "image_processor", None), "size", None)
    val = None
    if isinstance(size, dict):
        val = size.get(key)
    elif size is not None:  # transformers>=5 SizeDict-style object
        val = getattr(size, key, None)
        if val is None:
            try:
                val = size[key]
            except Exception:
                val = None
    if val is None:
        raise RuntimeError(
            f"Cannot resolve processor default for '{key}' from "
            f"image_processor.size={size!r}. Pass --min_pixels/--max_pixels explicitly.")
    return {"value": int(val), "source": f"processor.image_processor.size['{key}']"}


def _logprob_summary(completion: Any, top_n: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "cumulative_logprob": getattr(completion, "cumulative_logprob", None),
        "mean_logprob": None,
        "first_token_top": None,
    }
    try:
        n_tok = len(completion.token_ids) if completion.token_ids is not None else 0
        if out["cumulative_logprob"] is not None and n_tok:
            out["mean_logprob"] = out["cumulative_logprob"] / n_tok
        lps = getattr(completion, "logprobs", None)
        if lps:
            first = lps[0]
            items = []
            for tid, lp in first.items():
                items.append({
                    "token_id": int(tid),
                    "token": getattr(lp, "decoded_token", None),
                    "logprob": float(getattr(lp, "logprob", float("nan"))),
                    "rank": getattr(lp, "rank", None),
                })
            items.sort(key=lambda x: -x["logprob"])
            out["first_token_top"] = items[:top_n]
            # min per-token logprob of the sampled path (how "surprised" the
            # model was at its worst step) -- cheap extra signal.
            sampled = []
            for step, tid in zip(lps, completion.token_ids or []):
                if step and tid in step:
                    sampled.append(float(step[tid].logprob))
            if sampled:
                out["min_token_logprob"] = min(sampled)
                out["num_tokens_below_-5"] = sum(1 for x in sampled if x < -5.0)
    except Exception as exc:  # never let diagnostics kill the run
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def _timing_summary(output: Any) -> Dict[str, Any]:
    """Per-request timing from vLLM's RequestStateStats (needs
    disable_log_stats=False). All fields optional."""
    m = getattr(output, "metrics", None)
    if m is None:
        return {}
    t: Dict[str, Any] = {}
    for k in ["arrival_time", "queued_ts", "scheduled_ts", "first_token_ts",
              "last_token_ts", "first_token_latency"]:
        v = getattr(m, k, None)
        if v:
            t[k] = float(v)
    try:
        if "first_token_ts" in t and "last_token_ts" in t:
            t["decode_seconds"] = t["last_token_ts"] - t["first_token_ts"]
        if "queued_ts" in t and "scheduled_ts" in t:
            t["queue_seconds"] = t["scheduled_ts"] - t["queued_ts"]
    except Exception:
        pass
    return t


def _image_records(sample: Dict[str, Any], vllm_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Original + resized sizes and visual-token count per image, in the
    order the images appear in the prompt (<image N> reference order)."""
    recs: List[Dict[str, Any]] = []
    resized = vllm_input.get("multi_modal_data", {}).get("image") or []
    originals: List[Any] = []
    try:
        for msg in build_messages(sample):
            for item in msg["content"]:
                if item.get("type") == "image":
                    originals.append(item["image"])
    except Exception:
        originals = []
    for i, img in enumerate(resized):
        try:
            w, h = img.size
        except Exception:
            continue
        rec: Dict[str, Any] = {
            "resized_w": w, "resized_h": h,
            "visual_tokens": (w // VISUAL_TOKEN_SIDE) * (h // VISUAL_TOKEN_SIDE),
        }
        if i < len(originals):
            try:
                ow, oh = originals[i].size
                rec["orig_w"], rec["orig_h"] = ow, oh
            except Exception:
                pass
        recs.append(rec)
    return recs


def build_record(sample: Dict[str, Any], output: Any, vllm_input: Dict[str, Any],
                 args: argparse.Namespace, subject_seconds: float) -> Dict[str, Any]:
    completion = output.outputs[0]
    raw_response = completion.text
    options = parse_options(sample["options"])
    prediction = parse_answer(raw_response, sample["question_type"], options)

    record: Dict[str, Any] = {
        "id": sample["id"],
        "subject": sample["subject"],
        "question_type": sample["question_type"],
        "gold": sample["answer"],
        "options": options,
        "prediction_raw": raw_response,
        "prediction": prediction,

        # Generation diagnostics
        "prompt_tokens": (len(output.prompt_token_ids)
                          if getattr(output, "prompt_token_ids", None) is not None
                          else None),
        "completion_tokens": (len(completion.token_ids)
                              if completion.token_ids is not None else None),
        "finish_reason": completion.finish_reason,
        "stop_reason": getattr(completion, "stop_reason", None),
        "logprob_summary": _logprob_summary(completion, max(args.logprobs, 1)),
        "timing": _timing_summary(output),
        "subject_batch_seconds": subject_seconds,

        # Inputs
        "num_images": len(sample["images"]),
        "images": _image_records(sample, vllm_input),
        "prompt_text": None if args.no_prompt_text else vllm_input["prompt"],

        # Dataset metadata (for slicing in later analysis)
        "subfield": sample.get("subfield", ""),
        "img_type": sample.get("img_type", ""),
        "topic_difficulty": sample.get("topic_difficulty", ""),
        "explanation": sample.get("explanation", ""),
    }
    record["correct"] = is_correct(record)
    return record


def error_record(sample: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
    options = parse_options(sample["options"])
    rec = {
        "id": sample["id"], "subject": sample["subject"],
        "question_type": sample["question_type"], "gold": sample["answer"],
        "options": options, "prediction_raw": "", "prediction": None,
        "prompt_tokens": None, "completion_tokens": None,
        "finish_reason": "error", "error": f"{type(exc).__name__}: {exc}",
        "num_images": len(sample["images"]),
        "subfield": sample.get("subfield", ""), "img_type": sample.get("img_type", ""),
        "topic_difficulty": sample.get("topic_difficulty", ""),
        "explanation": sample.get("explanation", ""),
    }
    rec["correct"] = False
    return rec


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(path)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def generation_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    toks = [r["completion_tokens"] for r in results
            if r.get("completion_tokens") is not None]
    toks_sorted = sorted(toks)

    def pct(p: float) -> Optional[int]:
        if not toks_sorted:
            return None
        return toks_sorted[min(len(toks_sorted) - 1, int(p * len(toks_sorted)))]

    return {
        "finish_reason": dict(Counter(r.get("finish_reason") for r in results)),
        "prediction_none": sum(1 for r in results if r.get("prediction") is None),
        "errors": sum(1 for r in results if r.get("error")),
        "completion_tokens": {
            "mean": (sum(toks) / len(toks)) if toks else None,
            "median": pct(0.5), "p90": pct(0.9), "p99": pct(0.99),
            "max": max(toks) if toks else None,
            "sum": sum(toks),
        },
        "prompt_tokens_mean": (
            sum(r["prompt_tokens"] for r in results if r.get("prompt_tokens"))
            / max(1, sum(1 for r in results if r.get("prompt_tokens")))
        ),
    }


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    args = parse_args()
    start_time = time.perf_counter()
    start_iso = _dt.datetime.now().astimezone().isoformat(timespec="seconds")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for this baseline.")

    tensor_parallel_size = args.tensor_parallel_size
    if tensor_parallel_size is None:
        tensor_parallel_size = torch.cuda.device_count()
    if tensor_parallel_size < 1:
        raise RuntimeError("No CUDA device was detected.")

    # ---- output layout -------------------------------------------------
    run_dir = Path(args.run_dir) if args.run_dir else None
    output_path = Path(args.output_file) if args.output_file else (
        run_dir / "predictions.jsonl" if run_dir else Path("results/mmmu_predictions.jsonl"))
    metrics_path = Path(args.metrics_file) if args.metrics_file else (
        run_dir / "metrics.json" if run_dir else Path("results/mmmu_metrics.json"))
    manifest_path = (run_dir / "manifest.json") if run_dir else metrics_path.with_name(
        metrics_path.stem + "_manifest.json")
    per_subject_dir = (run_dir / "per_subject") if run_dir else output_path.with_name(
        output_path.stem + "_per_subject")
    for p in [output_path.parent, metrics_path.parent, per_subject_dir]:
        p.mkdir(parents=True, exist_ok=True)

    vram_poller = VRAMPoller(interval_sec=0.5)
    vram_poller.start()

    env = collect_environment()

    print("=" * 80)
    print("MMMU Validation Baseline")
    print("=" * 80)
    print(f"Model:       {args.model_path}")
    print(f"Revision:    {MODEL_REVISION}")
    print(f"Dataset:     {DATASET_NAME} @ {DATASET_REVISION}")
    print(f"Data cache:  {args.data_root}")
    print(f"TP size:     {tensor_parallel_size}")
    print(f"Run dir:     {run_dir}")
    print(f"Host/GPU:    {env['hostname']} / {[g['name'] for g in env['gpus']]}")
    print(f"Git:         {env['git_branch']}@{env['git_commit']} dirty={env['git_dirty']}")
    print(f"Started:     {start_iso}")
    print("=" * 80, flush=True)

    # ---- 1. dataset ----------------------------------------------------
    subjects = (args.subjects.split(",") if args.subjects else None)
    samples = load_mmmu_validation(data_root=args.data_root, subjects=subjects)

    if args.question_types:
        keep = set(args.question_types.split(","))
        samples = [x for x in samples if x["question_type"] in keep]
        print(f"[ABLATION] question_types={sorted(keep)} -> {len(samples)} samples")
    if args.img_types:
        want = [t.strip() for t in args.img_types.split(",") if t.strip()]
        samples = [x for x in samples if any(t in str(x.get("img_type", "")) for t in want)]
        print(f"[ABLATION] img_types={want} -> {len(samples)} samples")
    prompt_mod.NO_IMAGES = args.no_images
    if args.no_images:
        print("[ABLATION] no_images: every image replaced by the text '[image]'")
    prompt_mod.PROMPT_VARIANT = args.prompt_variant
    if args.prompt_variant != "official":
        print(f"[ABLATION] prompt_variant={args.prompt_variant}: "
              f"{PROMPT_VARIANTS[args.prompt_variant]}")

    if args.max_samples is not None:
        if args.max_samples <= 0:
            raise ValueError("--max_samples must be positive.")
        samples = samples[: args.max_samples]
        print(f"[DEBUG] Processing only {len(samples)} samples. "
              "Do not use this option for the final 900-sample report.")
    print(f"Loaded samples: {len(samples)}", flush=True)

    # ---- 2. model + processor -----------------------------------------
    print("Loading processor...", flush=True)
    looks_local = args.model_path.startswith(("/", "./", "../", "~"))
    if looks_local and not os.path.isdir(os.path.expanduser(args.model_path)):
        raise FileNotFoundError(
            f"--model_path {args.model_path} looks like a local path but no such directory "
            "exists (did the LoRA merge step fail?).")
    # A local directory (e.g. a merged LoRA checkpoint) has no hub revision.
    model_revision = None if os.path.isdir(args.model_path) else MODEL_REVISION
    print(f"Model revision: {model_revision or 'local checkpoint ' + os.path.abspath(args.model_path)}")
    processor = AutoProcessor.from_pretrained(args.model_path, revision=model_revision)

    min_px = resolve_pixels(args.min_pixels, processor, "shortest_edge", MIN_PIXELS)
    max_px = resolve_pixels(args.max_pixels, processor, "longest_edge", MAX_PIXELS)
    print(f"min_pixels = {min_px['value']} (~{min_px['value']/1e6:.3f} MP, "
          f"{min_px['value']//(VISUAL_TOKEN_SIDE**2)} visual tokens)  <- {min_px['source']}")
    print(f"max_pixels = {max_px['value']} (~{max_px['value']/1e6:.3f} MP, "
          f"{max_px['value']//(VISUAL_TOKEN_SIDE**2)} visual tokens)  <- {max_px['source']}",
          flush=True)

    print("Loading vLLM model...", flush=True)
    llm_kwargs: Dict[str, Any] = dict(
        model=args.model_path,
        revision=model_revision,
        dtype="bfloat16",
        tensor_parallel_size=tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        trust_remote_code=True,
        seed=args.seed,
        limit_mm_per_prompt={"image": 32},
        # Keep per-request timing stats (RequestOutput.metrics) + periodic
        # throughput logs in run.log.
        disable_log_stats=False,
    )
    if args.max_num_seqs:
        llm_kwargs["max_num_seqs"] = args.max_num_seqs
    llm = LLM(**llm_kwargs)
    model_load_seconds = time.perf_counter() - start_time
    print(f"Model ready in {model_load_seconds:.1f}s", flush=True)

    # ---- 3. sampling params -------------------------------------------
    common = dict(max_tokens=args.max_new_tokens, seed=args.seed,
                  stop_token_ids=[151645, 151643])  # <|im_end|>, <|endoftext|>
    if args.logprobs > 0:
        common["logprobs"] = args.logprobs
    if args.greedy:
        sampling_params = SamplingParams(temperature=0.0, **common)
    else:
        sampling_params = SamplingParams(
            temperature=args.temperature, top_p=args.top_p, top_k=args.top_k,
            repetition_penalty=args.repetition_penalty,
            presence_penalty=args.presence_penalty, **common)

    sampling_doc = {
        "greedy": args.greedy, "seed": args.seed,
        "temperature": None if args.greedy else args.temperature,
        "top_p": None if args.greedy else args.top_p,
        "top_k": None if args.greedy else args.top_k,
        "repetition_penalty": None if args.greedy else args.repetition_penalty,
        "presence_penalty": None if args.greedy else args.presence_penalty,
        "max_new_tokens": args.max_new_tokens,
        "stop_token_ids": [151645, 151643],
        "logprobs": args.logprobs or None,
        "matches_official_instruct_recipe": (
            not args.greedy
            and args.seed == OFFICIAL_RECIPE["seed"]
            and args.temperature == OFFICIAL_RECIPE["temperature"]
            and args.top_p == OFFICIAL_RECIPE["top_p"]
            and args.top_k == OFFICIAL_RECIPE["top_k"]
            and args.repetition_penalty == OFFICIAL_RECIPE["repetition_penalty"]
            and args.presence_penalty == OFFICIAL_RECIPE["presence_penalty"]
            and args.max_new_tokens == OFFICIAL_RECIPE["out_seq_length"]),
        "is_baseline_setting": (
            not args.greedy and args.prompt_variant == "official"
            and not args.question_types and not args.subjects
            and not args.img_types and not args.no_images
            and args.max_samples is None),
        "official_recipe_source":
            "https://github.com/QwenLM/Qwen3-VL#evaluation-reproduction "
            "(Generation Hyperparameters -> Instruct models)",
    }
    print("Generation settings:")
    for k, v in sampling_doc.items():
        print(f"  {k}={v}")
    print(flush=True)

    # ---- manifest (written before inference so a crash still leaves it) --
    manifest: Dict[str, Any] = {
        "status": "running",
        "started_at": start_iso,
        "model": MODEL_NAME, "model_path": args.model_path,
        "model_revision": MODEL_REVISION,
        "dataset": DATASET_NAME, "dataset_revision": DATASET_REVISION,
        "split": "validation",
        "num_samples": len(samples),
        "args": vars(args),
        "resolved": {
            "min_pixels": min_px, "max_pixels": max_px,
            "tensor_parallel_size": tensor_parallel_size,
            "max_model_len": args.max_model_len,
            "gpu_memory_utilization": args.gpu_memory_utilization,
            "batch_mode": args.batch_mode,
        },
        "sampling": sampling_doc,
        "prompt_source": {
            "template": "MMMU official llava1.5.yaml-style prompt + Qwen3-VL chat template",
            "multiple_choice":
                "{question}\\n\\n(A) {opt}\\n(B) {opt}...\\n"
                "Answer with the option's letter from the given choices directly.",
            "open":
                "{question}\\n\\nAnswer the question using a single word or phrase.",
            "code": "code/prompt.py",
        },
        "prompt_variant": args.prompt_variant,
        "prompt_instructions": PROMPT_VARIANTS[args.prompt_variant],
        "question_types": args.question_types,
        "img_types": args.img_types,
        "no_images": args.no_images,
        "model_revision_used": model_revision,
        "parser": "code/parser.py (MMMU eval_utils.py adapted; no random fallback; no LLM judge)",
        "environment": env,
        "outputs": {
            "predictions": str(output_path), "metrics": str(metrics_path),
            "per_subject_dir": str(per_subject_dir),
        },
    }
    write_json(manifest_path, manifest)

    # ---- 4. inference (per subject or all) ----------------------------
    print("=" * 80)
    print(f"Running vLLM inference (batch_mode={args.batch_mode})...", flush=True)
    inference_start = time.perf_counter()

    ordered_subjects = [s for s in SUBJECTS if any(x["subject"] == s for x in samples)]
    groups: List[List[Dict[str, Any]]]
    if args.batch_mode == "subject":
        groups = [[x for x in samples if x["subject"] == s] for s in ordered_subjects]
    else:
        groups = [samples]

    results: List[Dict[str, Any]] = []
    subject_timing: Dict[str, Dict[str, Any]] = {}
    prompt_example: Optional[str] = None

    for group in groups:
        subject = group[0]["subject"] if args.batch_mode == "subject" else "ALL"
        ckpt = per_subject_dir / f"{subject}.jsonl"

        if args.resume and ckpt.exists():
            prev = read_jsonl(ckpt)
            if len(prev) == len(group):
                results.extend(prev)
                subject_timing[subject] = {
                    "seconds": prev[0].get("subject_batch_seconds"),
                    "num": len(prev), "resumed": True}
                print(f"[resume] {subject}: {len(prev)} records loaded from {ckpt}",
                      flush=True)
                continue

        t0 = time.perf_counter()
        inputs = [build_vllm_input(x, processor, min_px["value"], max_px["value"])
                  for x in tqdm(group, desc=f"Building prompts [{subject}]", leave=False)]
        if prompt_example is None:
            prompt_example = inputs[0]["prompt"]
            manifest["prompt_example"] = {"id": group[0]["id"], "prompt": prompt_example}
            write_json(manifest_path, manifest)
        prep_seconds = time.perf_counter() - t0

        t1 = time.perf_counter()
        group_records: List[Dict[str, Any]] = []
        try:
            outputs = llm.generate(inputs, sampling_params=sampling_params, use_tqdm=True)
            gen_seconds = time.perf_counter() - t1
            for x, out, inp in zip(group, outputs, inputs):
                group_records.append(build_record(x, out, inp, args, gen_seconds))
        except Exception as exc:
            # One bad prompt (e.g. longer than max_model_len) must not sink
            # the whole subject: fall back to one-by-one generation.
            print(f"!! batch generate failed for {subject}: {type(exc).__name__}: {exc}\n"
                  f"   falling back to per-sample generation", flush=True)
            for x, inp in zip(group, inputs):
                try:
                    out = llm.generate([inp], sampling_params=sampling_params,
                                       use_tqdm=False)[0]
                    group_records.append(build_record(x, out, inp, args, None))
                except Exception as exc2:
                    print(f"!! sample {x['id']} failed: {type(exc2).__name__}: {exc2}",
                          flush=True)
                    group_records.append(error_record(x, exc2))
            gen_seconds = time.perf_counter() - t1
            for r in group_records:
                r["subject_batch_seconds"] = gen_seconds

        results.extend(group_records)
        n_ok = sum(r["correct"] for r in group_records)
        toks = [r["completion_tokens"] or 0 for r in group_records]
        subject_timing[subject] = {
            "seconds": gen_seconds, "prep_seconds": prep_seconds,
            "num": len(group_records), "correct": n_ok,
            "accuracy": n_ok / len(group_records),
            "completion_tokens_sum": sum(toks),
            "completion_tokens_max": max(toks) if toks else 0,
            "finish_reason": dict(Counter(r["finish_reason"] for r in group_records)),
            "resumed": False,
        }
        write_jsonl(ckpt, group_records)

        done = len(results)
        running_acc = sum(r["correct"] for r in results) / done
        elapsed = time.perf_counter() - inference_start
        eta = elapsed / done * (len(samples) - done)
        print(f"[{subject:36s}] acc={n_ok:2d}/{len(group_records):2d} "
              f"time={gen_seconds:7.1f}s tok_max={max(toks) if toks else 0:6d} | "
              f"done {done}/{len(samples)} running_acc={running_acc*100:5.2f}% "
              f"elapsed={elapsed/60:6.1f}m eta={eta/60:6.1f}m", flush=True)

        # Partial metrics for monitoring (scripts/status_run.sh reads this).
        partial = evaluate(results)
        partial.update({"status": "running", "subject_timing": subject_timing,
                        "inference_seconds_so_far": elapsed,
                        "generation": generation_stats(results)})
        write_json(metrics_path.with_name(metrics_path.stem + "_partial.json"), partial)

    inference_elapsed = time.perf_counter() - inference_start
    print(f"Inference time: {inference_elapsed:.2f}s "
          f"({inference_elapsed / max(len(samples), 1):.2f}s/sample)")

    peak_vram_gb = vram_poller.stop()
    print(f"Peak VRAM (system-wide, all processes): {peak_vram_gb:.2f} GB")

    # ---- 5. evaluation --------------------------------------------------
    results.sort(key=lambda r: (SUBJECTS.index(r["subject"]), r["id"]))
    metrics = evaluate(results)
    metrics["model"] = MODEL_NAME
    metrics["model_path"] = args.model_path
    metrics["model_revision"] = MODEL_REVISION
    metrics["dataset"] = DATASET_NAME
    metrics["dataset_revision"] = DATASET_REVISION
    metrics["split"] = "validation"
    metrics["sampling"] = sampling_doc
    metrics["prompt_variant"] = args.prompt_variant
    metrics["question_types"] = args.question_types
    metrics["img_types"] = args.img_types
    metrics["no_images"] = args.no_images
    metrics["peak_vram_gb"] = peak_vram_gb
    metrics["image_pixels"] = {"min_pixels": min_px["value"], "max_pixels": max_px["value"],
                               "min_pixels_source": min_px["source"],
                               "max_pixels_source": max_px["source"]}
    metrics["elapsed_seconds"] = time.perf_counter() - start_time
    metrics["inference_seconds"] = inference_elapsed
    metrics["model_load_seconds"] = model_load_seconds
    metrics["subject_timing"] = subject_timing
    metrics["generation"] = generation_stats(results)
    metrics["by_question_type"] = {
        qt: {"num": n, "correct": c, "accuracy": c / n}
        for qt, (n, c) in {
            qt: (sum(1 for r in results if r["question_type"] == qt),
                 sum(1 for r in results if r["question_type"] == qt and r["correct"]))
            for qt in sorted({r["question_type"] for r in results})
        }.items()
    }
    metrics["by_difficulty"] = {
        d: {"num": n, "correct": c, "accuracy": c / n}
        for d, (n, c) in {
            d: (sum(1 for r in results if r.get("topic_difficulty") == d),
                sum(1 for r in results if r.get("topic_difficulty") == d and r["correct"]))
            for d in sorted({r.get("topic_difficulty", "") for r in results})
        }.items() if n
    }
    metrics["environment"] = env
    metrics["started_at"] = start_iso
    metrics["finished_at"] = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    metrics["status"] = "completed"

    # ---- 6. save -------------------------------------------------------
    write_jsonl(output_path, results)
    write_json(metrics_path, metrics)
    manifest.update({"status": "completed", "finished_at": metrics["finished_at"],
                     "overall_percent": metrics["overall_percent"],
                     "elapsed_seconds": metrics["elapsed_seconds"],
                     "peak_vram_gb": peak_vram_gb})
    write_json(manifest_path, manifest)
    partial_path = metrics_path.with_name(metrics_path.stem + "_partial.json")
    if partial_path.exists():
        partial_path.unlink()

    print("=" * 80)
    print("Results")
    print("=" * 80)
    for subject in SUBJECTS:
        if subject not in metrics["subjects"]:
            continue
        item = metrics["subjects"][subject]
        t = subject_timing.get(subject, {}).get("seconds")
        print(f"{subject:40s} {item['accuracy'] * 100:6.2f}% "
              f"({item['correct']}/{item['num']})"
              + (f"  {t:8.1f}s" if t else ""))
    print("-" * 80)
    print(f"Overall: {metrics['overall_percent']:.2f}%")
    print(f"Finish reasons: {metrics['generation']['finish_reason']}")
    print(f"Saved predictions: {output_path}")
    print(f"Saved metrics:     {metrics_path}")
    print(f"Saved manifest:    {manifest_path}")
    print(f"Total elapsed:     {metrics['elapsed_seconds']:.2f}s")


if __name__ == "__main__":
    main()
