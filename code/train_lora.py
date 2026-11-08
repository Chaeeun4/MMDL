"""
LoRA SFT for Qwen3-VL-4B-Instruct on one GPU (RTX 3090 24GB), built on the
feasibility loop in code/lora_smoke_train.py (same encoding: loss only on the
response tokens).

Data: jsonl from code/gen_rft.py select (never MMMU / MMMU-Pro):
    {"id", "images": ["/abs/path.png", ...], "prompt": "... <image 1> ...", "response": "... Answer: B"}

    python code/train_lora.py --train_jsonl /data/$USER/rft/pilot/sft.jsonl --out_dir /data/$USER/ckpt/c1_pilot
    python code/merge_lora.py --adapter /data/$USER/ckpt/c1_pilot/adapter --out /data/$USER/ckpt/c1_pilot_merged

--identity saves an untrained (B=0) adapter: merging it must reproduce the baseline
exactly, which rules out merge/eval bugs before reading any fine-tuning result.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lora_smoke_train import LANG_TARGET, MODEL_NAME, MODEL_REVISION, encode  # noqa: E402

TARGETS = {
    "language": LANG_TARGET,
    # language LoRA + the vision->LLM projectors (main merger and DeepStack mergers)
    "language_merger": LANG_TARGET[:-1] + r"|.*visual\.(merger|deepstack_merger_list\.\d+)\.linear_fc[12]$",
    # everything incl. the vision encoder blocks
    "all": "all-linear",
}


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_path", default=MODEL_NAME)
    ap.add_argument("--train_jsonl", default=None)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--grad_accum", type=int, default=16, help="batch size 1 x grad_accum")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--warmup", type=float, default=0.05, help="fraction of steps")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--target", choices=list(TARGETS), default="language")
    ap.add_argument("--min_pixels", type=int, default=256 * 32 * 32)
    ap.add_argument("--max_pixels", type=int, default=1280 * 32 * 32)
    ap.add_argument("--max_len", type=int, default=4096)
    ap.add_argument("--save_every", type=int, default=0, help="optimizer steps; 0 = only at the end")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--identity", action="store_true", help="save the untrained adapter and exit")
    return ap.parse_args()


def load_jsonl(path):
    recs = []
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            # qwen_vl_utils opens local paths itself, so images stay lazy
            recs.append({"id": r["id"], "prompt": r["prompt"], "response": r["response"],
                         "images": {i + 1: p for i, p in enumerate(r.get("images", []))}})
    return recs


def main():
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForImageTextToText, AutoProcessor

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rev = None if os.path.isdir(args.model_path) else MODEL_REVISION
    processor = AutoProcessor.from_pretrained(args.model_path, revision=rev)
    model = AutoModelForImageTextToText.from_pretrained(args.model_path, revision=rev, dtype=torch.bfloat16)
    cfg = LoraConfig(r=args.rank, lora_alpha=args.alpha, lora_dropout=0.05, task_type="CAUSAL_LM",
                     target_modules=TARGETS[args.target])
    if args.identity:
        get_peft_model(model, cfg).save_pretrained(out / "adapter")
        print(f"identity (untrained) adapter saved to {out / 'adapter'}")
        return

    free = torch.cuda.mem_get_info()[0] / 2 ** 30
    if free < 14:
        raise SystemExit(f"only {free:.1f} GiB GPU memory free; another job is using the GPU")
    model.to("cuda")
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, cfg)
    params = [p for p in model.parameters() if p.requires_grad]
    print(f"trainable params: {sum(p.numel() for p in params):,}")

    recs = load_jsonl(args.train_jsonl)
    total_steps = max(1, int(len(recs) * args.epochs) // args.grad_accum)
    warm = max(1, int(total_steps * args.warmup))
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / warm if s < warm else 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total_steps - warm))))
    print(f"records {len(recs)}, epochs {args.epochs}, optimizer steps {total_steps}", flush=True)
    (out / "train_args.json").write_text(json.dumps(vars(args), indent=2))

    model.train()
    torch.cuda.reset_peak_memory_stats()
    log_f = open(out / "train_log.jsonl", "a")
    step, micro, seen, skipped, ooms, acc_loss, t0 = 0, 0, 0, 0, 0, 0.0, time.perf_counter()
    order = []
    while step < total_steps:
        if not order:
            order = list(range(len(recs)))
            random.shuffle(order)
        rec = recs[order.pop()]
        seen += 1
        try:
            enc, _ = encode(rec, processor, args)
        except Exception as e:
            print(f"skip {rec['id']}: {type(e).__name__}: {e}")
            skipped += 1
            continue
        if enc["input_ids"].shape[1] > args.max_len:
            skipped += 1
            continue
        enc = {k: v.to("cuda") for k, v in enc.items()}
        try:
            loss = model(**enc).loss / args.grad_accum
            loss.backward()
        except torch.cuda.OutOfMemoryError:
            ooms += 1
            opt.zero_grad(set_to_none=True)
            micro, acc_loss = 0, 0.0
            torch.cuda.empty_cache()
            print(f"OOM (id={rec['id']}, len={enc['input_ids'].shape[1]})")
            continue
        acc_loss += loss.item()
        micro += 1
        if micro == args.grad_accum:
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            dt = time.perf_counter() - t0
            row = {"step": step, "loss": acc_loss, "lr": sched.get_last_lr()[0], "elapsed_s": round(dt),
                   "peak_gb": round(torch.cuda.max_memory_allocated() / 2 ** 30, 2)}
            log_f.write(json.dumps(row) + "\n")
            log_f.flush()
            eta = dt / step * (total_steps - step) / 60
            print(f"step {step}/{total_steps} loss {acc_loss:.4f} lr {row['lr']:.2e} "
                  f"peak {row['peak_gb']}GB eta {eta:.0f}min", flush=True)
            micro, acc_loss = 0, 0.0
            if args.save_every and step % args.save_every == 0:
                model.save_pretrained(out / f"adapter_step{step}")
    model.save_pretrained(out / "adapter")
    summary = {"steps": step, "samples_seen": seen, "skipped": skipped, "ooms": ooms,
               "hours": round((time.perf_counter() - t0) / 3600, 2),
               "peak_gb": round(torch.cuda.max_memory_allocated() / 2 ** 30, 2)}
    (out / "train_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), f"\nadapter saved to {out / 'adapter'}")


if __name__ == "__main__":
    main()
