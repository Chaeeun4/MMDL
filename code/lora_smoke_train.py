"""
LoRA feasibility test for Qwen3-VL-4B-Instruct on one GPU (e.g. RTX 3090 24GB).

Purpose: answer "can we fine-tune this model on our hardware, how fast, and how
much memory does it need?" before committing to a fine-tuning plan. It is NOT a
training recipe and the adapter it produces must NOT be used for reported results.

Data (pick one):
  --mmmu_dev_smoke         MMMU *dev* split (5 q/subject, 150 total, pinned revision).
                           Never the validation split, which is our evaluation set.
  --train_jsonl FILE       Your own data, one JSON object per line:
                           {"id": "...", "images": ["/abs/path.png", ...],
                            "prompt": "text with <image 1> placeholders ...",
                            "response": "step-by-step ... Answer: B"}

    python code/lora_smoke_train.py --mmmu_dev_smoke --max_steps 30 \
        --out_dir runs/lora_smoke --save_adapter

Writes <out_dir>/lora_smoke_summary.json (peak memory, s/step, trainable params,
token lengths, OOM count) and, with --save_adapter, <out_dir>/adapter/.
Then: python code/merge_lora.py --adapter <out_dir>/adapter --out <dir>
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import DATASET_NAME, DATASET_REVISION, SUBJECTS  # noqa: E402

MODEL_NAME = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"
IMG_RE = re.compile(r"<image\s+(\d+)>")
LANG_TARGET = r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)$"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_path", default=MODEL_NAME)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--mmmu_dev_smoke", action="store_true")
    src.add_argument("--train_jsonl", default=None)
    ap.add_argument("--data_root", default=os.environ.get("HF_HOME"))
    ap.add_argument("--out_dir", default="runs/lora_smoke")
    ap.add_argument("--max_steps", type=int, default=30)
    ap.add_argument("--grad_accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--target", choices=["language", "all"], default="language",
                    help="'language': LoRA on the LLM only. 'all': every linear layer "
                         "incl. the vision encoder (peft 'all-linear').")
    ap.add_argument("--min_pixels", type=int, default=64 * 32 * 32)
    ap.add_argument("--max_pixels", type=int, default=1280 * 32 * 32,
                    help="Training image budget (default 1280 visual tokens).")
    ap.add_argument("--max_len", type=int, default=4096, help="skip samples longer than this")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--save_adapter", action="store_true")
    ap.add_argument("--list_modules", action="store_true",
                    help="print Linear module names (to check LoRA targets) and exit")
    return ap.parse_args()


# ---------------------------------------------------------------- data
def mmmu_dev_records(data_root):
    from datasets import load_dataset
    from prompt import MC_DIRECT, OPEN_DIRECT, parse_options
    recs = []
    for subj in SUBJECTS:
        ds = load_dataset(DATASET_NAME, subj, split="dev", revision=DATASET_REVISION, cache_dir=data_root)
        for row in ds:
            opts = parse_options(row["options"])
            q = row["question"]
            if opts:
                q += "\n\n" + "\n".join(f"({chr(65 + i)}) {o}" for i, o in enumerate(opts)) + "\n" + MC_DIRECT
            else:
                q += "\n\n" + OPEN_DIRECT
            imgs = {int(k.split("_")[1]): row[k] for k in row if k.startswith("image_") and row[k] is not None}
            recs.append({"id": row["id"], "prompt": q, "images": imgs, "response": str(row["answer"])})
    return recs


def jsonl_records(path):
    from PIL import Image
    recs = []
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        imgs = {i + 1: Image.open(p).convert("RGB") for i, p in enumerate(r.get("images", []))}
        recs.append({"id": r.get("id"), "prompt": r["prompt"], "images": imgs, "response": r["response"]})
    return recs


def to_messages(rec, min_px, max_px):
    content: List[Dict[str, Any]] = []
    cur = 0
    used = set()
    for m in IMG_RE.finditer(rec["prompt"]):
        if m.start() > cur:
            content.append({"type": "text", "text": rec["prompt"][cur:m.start()]})
        idx = int(m.group(1))
        content.append({"type": "image", "image": rec["images"][idx], "min_pixels": min_px, "max_pixels": max_px})
        used.add(idx)
        cur = m.end()
    if cur < len(rec["prompt"]):
        content.append({"type": "text", "text": rec["prompt"][cur:]})
    # images not referenced in the text go first, in order
    extra = [{"type": "image", "image": rec["images"][i], "min_pixels": min_px, "max_pixels": max_px}
             for i in sorted(rec["images"]) if i not in used]
    return [{"role": "user", "content": extra + content}]


def encode(rec, processor, args):
    from qwen_vl_utils import process_vision_info
    msgs = to_messages(rec, args.min_pixels, args.max_pixels)
    prompt_text = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    full_text = prompt_text + rec["response"] + "<|im_end|>\n"
    images, _ = process_vision_info(msgs, image_patch_size=processor.image_processor.patch_size)
    enc = processor(text=[full_text], images=images, return_tensors="pt")
    p_len = processor(text=[prompt_text], images=images, return_tensors="pt")["input_ids"].shape[1]
    labels = enc["input_ids"].clone()
    labels[:, :p_len] = -100
    enc["labels"] = labels
    return enc, p_len


# ---------------------------------------------------------------- main
def main():
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from peft import LoraConfig, get_peft_model

    free, total = torch.cuda.mem_get_info()
    if free < 14 * 2 ** 30:
        raise SystemExit(f"Only {free / 2 ** 30:.1f} GiB of {total / 2 ** 30:.1f} GiB GPU memory is free. "
                         "Another job (e.g. a vLLM evaluation) is using the GPU; run this after it finishes.")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rev = None if os.path.isdir(args.model_path) else MODEL_REVISION
    processor = AutoProcessor.from_pretrained(args.model_path, revision=rev)
    model = AutoModelForImageTextToText.from_pretrained(args.model_path, revision=rev, dtype=torch.bfloat16)

    if args.list_modules:
        names = [n for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)]
        print("\n".join(names[:60]), f"\n... {len(names)} Linear modules total")
        print("language-target matches:", sum(bool(re.fullmatch(LANG_TARGET, n)) for n in names))
        return

    model.to("cuda")
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    cfg = LoraConfig(r=args.rank, lora_alpha=args.alpha, lora_dropout=0.05, task_type="CAUSAL_LM",
                     target_modules=LANG_TARGET if args.target == "language" else "all-linear")
    model = get_peft_model(model, cfg)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"trainable params: {trainable:,} / {total:,} ({trainable / total * 100:.3f}%)")

    recs = mmmu_dev_records(args.data_root) if (args.mmmu_dev_smoke or not args.train_jsonl) else jsonl_records(args.train_jsonl)
    random.shuffle(recs)
    print(f"records: {len(recs)}")

    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    model.train()
    torch.cuda.reset_peak_memory_stats()
    log, ooms, skipped, step, micro = [], 0, 0, 0, 0
    t_step = time.perf_counter()
    lens = []
    i = 0
    while step < args.max_steps and recs:
        rec = recs[i % len(recs)]
        i += 1
        try:
            enc, p_len = encode(rec, processor, args)
        except Exception as e:  # bad sample should not stop a feasibility test
            print(f"skip {rec['id']}: {type(e).__name__}: {e}")
            skipped += 1
            continue
        L = enc["input_ids"].shape[1]
        if L > args.max_len:
            skipped += 1
            continue
        enc = {k: v.to("cuda") for k, v in enc.items()}
        try:
            loss = model(**enc).loss / args.grad_accum
            loss.backward()
        except torch.cuda.OutOfMemoryError:
            ooms += 1
            opt.zero_grad(set_to_none=True)
            torch.cuda.empty_cache()
            print(f"OOM at seq_len={L} (id={rec['id']})")
            continue
        lens.append(L)
        micro += 1
        if micro % args.grad_accum == 0:
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            dt = time.perf_counter() - t_step
            t_step = time.perf_counter()
            mem = torch.cuda.max_memory_allocated() / 2 ** 30
            log.append({"step": step, "loss": loss.item() * args.grad_accum, "sec": dt, "peak_gb": mem})
            print(f"step {step:3d} loss {log[-1]['loss']:.4f} {dt:6.1f}s/step peak {mem:5.2f} GB")

    summary = {
        "model": args.model_path, "target": args.target, "rank": args.rank, "lr": args.lr,
        "grad_accum": args.grad_accum, "max_pixels": args.max_pixels, "max_len": args.max_len,
        "data": args.train_jsonl or "mmmu_dev_smoke",
        "trainable_params": trainable, "total_params": total,
        "steps": step, "ooms": ooms, "skipped": skipped,
        "peak_mem_gb": torch.cuda.max_memory_allocated() / 2 ** 30,
        "sec_per_step_mean": (sum(x["sec"] for x in log[1:]) / max(1, len(log) - 1)) if log else None,
        "seq_len": {"mean": sum(lens) / len(lens) if lens else None, "max": max(lens) if lens else None},
        "loss_first": log[0]["loss"] if log else None, "loss_last": log[-1]["loss"] if log else None,
        "gpu": torch.cuda.get_device_name(0), "log": log,
    }
    if summary["sec_per_step_mean"]:
        s = summary["sec_per_step_mean"] / args.grad_accum
        summary["est_hours_per_1k_samples"] = s * 1000 / 3600
    (out / "lora_smoke_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "log"}, indent=2))
    if args.save_adapter:
        model.save_pretrained(out / "adapter")
        print(f"adapter saved to {out / 'adapter'}")


if __name__ == "__main__":
    main()
