"""
Merge a LoRA adapter into the bf16 base model and save a normal checkpoint that
code/run_mmmu.py can evaluate with --model_path <out> (same pipeline as baseline).

    python code/merge_lora.py --adapter runs/lora_smoke/adapter --out /data/$USER/ckpt/lora_smoke_merged
"""
import argparse
import os

import torch
from peft import PeftModel
from transformers import AutoModelForImageTextToText, AutoProcessor

MODEL_NAME = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"

ap = argparse.ArgumentParser()
ap.add_argument("--adapter", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--base", default=MODEL_NAME)
a = ap.parse_args()

rev = None if os.path.isdir(a.base) else MODEL_REVISION
base = AutoModelForImageTextToText.from_pretrained(a.base, revision=rev, dtype=torch.bfloat16)
merged = PeftModel.from_pretrained(base, a.adapter).merge_and_unload()
merged.save_pretrained(a.out, safe_serialization=True)
AutoProcessor.from_pretrained(a.base, revision=rev).save_pretrained(a.out)
with open(os.path.join(a.out, "MERGED_FROM.txt"), "w") as f:
    f.write(f"base={a.base}@{rev}\nadapter={os.path.abspath(a.adapter)}\n")
print(f"merged checkpoint written to {a.out}")
