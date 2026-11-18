from __future__ import annotations

import datasets
try:
    datasets.config.HF_DATASETS_TRUST_REMOTE_CODE = True
except Exception:
    pass

"""
One-command Qwen3-VL-4B-Instruct MMMU validation evaluation.

Pipeline:
    HF MMMU validation
        -> official-style MMMU prompt
        -> Qwen3-VL inference with vLLM
        -> deterministic MMMU-style parser
        -> gold/prediction result records
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
"""


import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import torch
from tqdm import tqdm
from transformers import AutoProcessor
from vllm import LLM, SamplingParams

from dataset import DATASET_REVISION, SUBJECTS, load_mmmu_validation
from evaluator import evaluate, is_correct
from parser import parse_answer
from prompt import MAX_PIXELS, MIN_PIXELS, PROMPT_VARIANTS, build_vllm_input, parse_options

import subprocess
import threading


MODEL_NAME = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"

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
    

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the complete MMMU validation baseline in one command."
    )

    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="HF model ID or a local merged model directory.",
    )
    parser.add_argument(
        "--data_root",
        type=str,
        required=True,
        help="Local Hugging Face cache directory for MMMU.",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="JSONL prediction/result file.",
    )
    parser.add_argument(
        "--metrics_file",
        type=str,
        default=None,
        help="JSON metrics output file.",
    )
    parser.add_argument("--run_dir", type=Path, help="Directory for predictions.jsonl and metrics.json.")
    parser.add_argument(
        "--subjects", help="Comma-separated MMMU subjects, e.g. Music or Music,Chemistry."
    )
    parser.add_argument(
        "--prompt_variant", choices=(*PROMPT_VARIANTS, "legacy_cot"), default="official",
        help="Instruction wording. official matches jina's model-card baseline.",
    )

    # Assignment generation recipe from Qwen3-VL official evaluation docs.
    parser.add_argument(
        "--greedy",
        action="store_true",
        default=False,
        help=(
            "Use greedy decoding (temperature=0) instead of the official "
            "sampling recipe below. The official Qwen3-VL evaluation "
            "reproduction script sets greedy='false', so leave this unset "
            "for the assignment run; it exists only for ablation/debugging."
        ),
    )
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top_p", type=float, default=0.8)
    parser.add_argument("--top_k", type=int, default=20)
    parser.add_argument("--repetition_penalty", type=float, default=1.0)
    parser.add_argument("--presence_penalty", type=float, default=1.5)
    parser.add_argument("--max_new_tokens", type=int, default=32768)

    # Qwen3-VL visual token budget (per-image resolution range fed to
    # qwen-vl-utils / vLLM). Exposed here instead of hardcoded in prompt.py
    # so it's documented and tunable without editing source.
    parser.add_argument("--min_pixels", default=MIN_PIXELS, help="Integer pixel limit or auto.")
    parser.add_argument("--max_pixels", default=MAX_PIXELS, help="Integer pixel limit or auto.")

    # vLLM / context settings.
    parser.add_argument(
        "--max_model_len",
        type=int,
        default=32768,
        help="Maximum model context length.",
    )
    parser.add_argument(
        "--gpu_memory_utilization",
        type=float,
        default=0.90,
    )
    parser.add_argument(
        "--tensor_parallel_size",
        type=int,
        default=None,
        help="Defaults to the number of visible CUDA devices.",
    )
    parser.add_argument("--max_num_seqs", type=int, help="vLLM maximum concurrent sequences.")
    parser.add_argument(
        "--batch_mode", choices=("subject", "all"), default="all",
        help="Generate separately per subject or in one batch.",
    )
    parser.add_argument("--logprobs", type=int, default=0)

    # Optional debugging only. Normal assignment run must leave this unset.
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Debug only: evaluate only the first N samples.",
    )

    args = parser.parse_args()
    if args.subjects is not None:
        requested = [subject.strip() for subject in args.subjects.split(",")]
        unknown = set(requested) - set(SUBJECTS)
        if unknown:
            parser.error(f"unknown subjects: {', '.join(repr(name) for name in sorted(unknown))}")
        args.subjects = [subject for subject in SUBJECTS if subject in requested]
    if args.max_samples is not None and args.max_samples <= 0:
        parser.error("--max_samples must be positive")
    if args.logprobs < 0:
        parser.error("--logprobs must be nonnegative")
    return args


def resolve_pixels(value: str | int, processor: Any, key: str) -> int:
    if value != "auto":
        return int(value)
    size = getattr(processor.image_processor, "size", None)
    resolved = size.get(key) if isinstance(size, dict) else getattr(size, key, None)
    if resolved is None:
        raise ValueError(f"Processor has no {key!r} pixel limit. Pass an explicit pixel limit.")
    return int(resolved)


def prepare_model_inputs(
    samples: List[Dict[str, Any]],
    processor: Any,
    min_pixels: int,
    max_pixels: int,
    prompt_variant: str,
) -> List[Dict[str, Any]]:
    inputs = []

    for sample in tqdm(samples, desc="Building multimodal prompts"):
        inputs.append(
            build_vllm_input(sample, processor, min_pixels, max_pixels, prompt_variant)
        )

    return inputs


def main() -> None:
    args = parse_args()
    start_time = time.perf_counter()
    model_path = Path(args.model_path)
    if (model_path / "adapter_config.json").is_file():
        raise ValueError("Merge the LoRA adapter into the base model before passing it to --model_path.")
    model_revision = None if model_path.is_dir() else MODEL_REVISION

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for this baseline.")

    tensor_parallel_size = args.tensor_parallel_size
    if tensor_parallel_size is None:
        tensor_parallel_size = torch.cuda.device_count()

    if tensor_parallel_size < 1:
        raise RuntimeError("No CUDA device was detected.")

    
    # Peak VRAM across model load + inference, measured system-wide via
    # nvidia-smi (captures vLLM's EngineCore subprocess too, unlike
    # torch.cuda APIs which only see the calling process).
    vram_poller = VRAMPoller(interval_sec=0.5)
    vram_poller.start()

    print("=" * 80)
    print("MMMU Validation Baseline")
    print("=" * 80)
    print(f"Model:       {args.model_path}")
    print(f"Revision:    {model_revision or '(local checkpoint)'}")
    print(f"Dataset:     MMMU/MMMU")
    print(f"Data cache:  {args.data_root}")
    print(f"TP size:     {tensor_parallel_size}")
    print("=" * 80)

    # 1. Dataset
    import datasets
    import sys

    print("\n[DEBUG]")
    print("Python:", sys.executable)
    print("Datasets:", datasets.__version__)
    print("Dataset function:", load_mmmu_validation.__code__.co_filename)
    print("Data root:", repr(args.data_root))
    print("[DEBUG END]\n")
    samples = load_mmmu_validation(data_root=args.data_root, subjects=args.subjects)

    if args.max_samples is not None:
        samples = samples[: args.max_samples]
        print(
            f"[DEBUG] Processing only {len(samples)} samples. "
            "Do not use this option for the final 900-sample report."
        )

    print(f"Loaded samples: {len(samples)}")

    # 2. Model + processor
    print("Loading processor...")
    processor = AutoProcessor.from_pretrained(
        args.model_path,
        revision=model_revision,
    )
    min_pixels = resolve_pixels(args.min_pixels, processor, "shortest_edge")
    max_pixels = resolve_pixels(args.max_pixels, processor, "longest_edge")
    if not 0 < min_pixels <= max_pixels:
        raise ValueError("Pixel limits must satisfy 0 < min_pixels <= max_pixels.")

    print("Loading vLLM model...")
    engine_options = {}
    if args.max_num_seqs is not None:
        engine_options["max_num_seqs"] = args.max_num_seqs
    llm = LLM(
        model=args.model_path,
        revision=model_revision,
        dtype="bfloat16",
        tensor_parallel_size=tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        trust_remote_code=True,
        seed=args.seed,
        limit_mm_per_prompt={"image": 32},
        **engine_options,
    )

    # 3. Generation parameters
    sampling_options = {}
    if args.logprobs:
        sampling_options["logprobs"] = args.logprobs

    if args.greedy:
        # temperature=0.0 makes vLLM pick the argmax token every step, which
        # makes top_p/top_k/repetition_penalty/presence_penalty moot.
        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=args.max_new_tokens,
            seed=args.seed,
            **sampling_options,
        )
    else:
        sampling_params = SamplingParams(
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            max_tokens=args.max_new_tokens,
            repetition_penalty=args.repetition_penalty,
            presence_penalty=args.presence_penalty,
            stop_token_ids=[151645, 151643], # 👈 Qwen 종료 토큰 명시적 추가
            seed=args.seed,
            **sampling_options,
        )

    print("Generation settings:")
    print(f"  greedy={args.greedy}")
    print(f"  seed={args.seed}")
    print(f"  prompt_variant={args.prompt_variant}")
    if args.greedy:
        print(
            "  (temperature/top_p/top_k/repetition_penalty/presence_penalty "
            "ignored under greedy decoding)"
        )
    else:
        print(f"  temperature={args.temperature}")
        print(f"  top_p={args.top_p}")
        print(f"  top_k={args.top_k}")
        print(f"  repetition_penalty={args.repetition_penalty}")
        print(f"  presence_penalty={args.presence_penalty}")
    print(f"  max_new_tokens={args.max_new_tokens}")
    print(f"  min_pixels={min_pixels} (~{min_pixels / 1e6:.2f} MP)")
    print(f"  max_pixels={max_pixels} (~{max_pixels / 1e6:.2f} MP)")

    # 4. Inference
    print("=" * 80)
    print("Running vLLM inference...")
    by_subject = {}
    for sample in samples:
        by_subject.setdefault(sample["subject"], []).append(sample)
    groups = by_subject.values() if args.batch_mode == "subject" else [samples]
    outputs = []
    inference_elapsed = 0.0
    for group in groups:
        inputs = prepare_model_inputs(group, processor, min_pixels, max_pixels, args.prompt_variant)
        inference_start = time.perf_counter()
        batch_outputs = llm.generate(inputs, sampling_params=sampling_params, use_tqdm=True)
        inference_elapsed += time.perf_counter() - inference_start
        if len(batch_outputs) != len(group):
            raise RuntimeError(f"Expected {len(group)} outputs, got {len(batch_outputs)}.")
        outputs.extend(batch_outputs)
    print(
        f"Inference time: {inference_elapsed:.2f}s "
        f"({inference_elapsed / max(len(samples), 1):.2f}s/sample)"
    )

    # Peak VRAM across model load + inference, measured system-wide via
    # nvidia-smi (see VRAMPoller docstring).
    peak_vram_gb = vram_poller.stop()
    print(f"Peak VRAM (system-wide, all processes): {peak_vram_gb:.2f} GB")

    # 5. Parse + preserve dataset gold answer
    results: List[Dict[str, Any]] = []

    for sample, output in zip(samples, outputs):
        completion = output.outputs[0]

        raw_response = completion.text

        # vLLM generation metadata
        completion_tokens = (
            len(completion.token_ids)
            if completion.token_ids is not None
            else None
        )
        finish_reason = completion.finish_reason

        options = parse_options(sample["options"])

        prediction = parse_answer(
            raw_response,
            sample["question_type"],
            options,
            strict=False,
        )

        result: Dict[str, Any] = {
            "id": sample["id"],
            "subject": sample["subject"],
            "question_type": sample["question_type"],
            "gold": sample["answer"],
            "options": options,
            "prediction_raw": raw_response,
            "prediction": prediction,

            # Generation diagnostics
            "completion_tokens": completion_tokens,
            "finish_reason": finish_reason,

            "subfield": sample.get("subfield", ""),
            "img_type": sample.get("img_type", ""),
            "topic_difficulty": sample.get("topic_difficulty", ""),
        }
        if args.logprobs:
            result["cumulative_logprob"] = completion.cumulative_logprob
        result["correct"] = is_correct(result)
        results.append(result)

    # 6. Evaluation
    metrics = evaluate(results)
    metrics["model"] = MODEL_NAME
    metrics["model_path"] = args.model_path
    metrics["model_revision"] = model_revision
    metrics["dataset"] = "MMMU/MMMU"
    metrics["dataset_revision"] = DATASET_REVISION
    metrics["split"] = "validation"
    metrics["evaluated_subjects"] = list(by_subject)
    metrics["max_samples"] = args.max_samples
    metrics["prompt_variant"] = args.prompt_variant
    metrics["batch_mode"] = args.batch_mode
    metrics["max_model_len"] = args.max_model_len
    metrics["max_num_seqs"] = args.max_num_seqs
    metrics["tensor_parallel_size"] = tensor_parallel_size
    metrics["gpu_memory_utilization"] = args.gpu_memory_utilization
    metrics["sampling"] = {
        "greedy": args.greedy,
        "seed": args.seed,
        "temperature": None if args.greedy else args.temperature,
        "top_p": None if args.greedy else args.top_p,
        "top_k": None if args.greedy else args.top_k,
        "repetition_penalty": None if args.greedy else args.repetition_penalty,
        "presence_penalty": None if args.greedy else args.presence_penalty,
        "max_new_tokens": args.max_new_tokens,
        "logprobs": args.logprobs,
    }
    metrics["peak_vram_gb"] = peak_vram_gb
    metrics["image_pixels"] = {
        "min_pixels": min_pixels,
        "max_pixels": max_pixels,
    }
    metrics["elapsed_seconds"] = time.perf_counter() - start_time
    metrics["inference_seconds"] = inference_elapsed

    # 7. Save
    output_path = Path(args.output_file) if args.output_file else (
        args.run_dir / "predictions.jsonl" if args.run_dir else Path("results/mmmu_predictions.jsonl")
    )
    metrics_path = Path(args.metrics_file) if args.metrics_file else (
        args.run_dir / "metrics.json" if args.run_dir else Path("results/mmmu_metrics.json")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("Results")
    print("=" * 80)

    for subject in SUBJECTS:
        if subject not in metrics["subjects"]:
            continue
        item = metrics["subjects"][subject]
        print(
            f"{subject:40s} "
            f"{item['accuracy'] * 100:6.2f}% "
            f"({item['correct']}/{item['num']})"
        )

    print("-" * 80)
    scope = "Overall" if len(results) == 900 else f"Selected subset ({len(results)} samples)"
    print(f"{scope}: {metrics['overall_percent']:.2f}%")
    print(f"Saved predictions: {output_path}")
    print(f"Saved metrics:     {metrics_path}")
    print(f"Total elapsed:     {metrics['elapsed_seconds']:.2f}s")


if __name__ == "__main__":
    main()
