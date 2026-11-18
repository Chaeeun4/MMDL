#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python_bin="${PYTHON_BIN:-python3}"
data_root="${MMMU_CACHE:-${HF_HOME:-/workspace/huggingface_cache}}"
checkpoint_root="${CHECKPOINT_ROOT:-/shared_dir/outputs}"
merge_root="${MERGE_ROOT:-/shared_dir/tmp_merged}"
run_root="runs/sweep_60q"
summary="$run_root/summary.csv"
base_model="${BASE_MODEL_PATH:-Qwen/Qwen3-VL-4B-Instruct}"
variants=(official legacy_cot describe_cot)

if [[ -n "${BASE_MODEL_PATH:-}" ]]; then
    if [[ ! -f "$base_model/config.json" ]]; then
        printf 'BASE_MODEL_PATH must point to a downloaded model snapshot: %s\n' "$base_model" >&2
        exit 1
    fi
    base_model=$(realpath -- "$base_model")
fi

export VLLM_WORKER_MULTIPROC_METHOD="${VLLM_WORKER_MULTIPROC_METHOD:-spawn}"

# Each entry is model:step:adapter subdirectory. An empty suffix is the final adapter.
targets=(
    base:0:
    primus_only:100:checkpoint-100 primus_only:200:checkpoint-200
    primus_only:300:checkpoint-300 primus_only:400:checkpoint-400 primus_only:500:
    pubchem_only:250:checkpoint-250 pubchem_only:500:checkpoint-500
    pubchem_only:750:checkpoint-750 pubchem_only:1000:checkpoint-1000 pubchem_only:1188:
    both:350:checkpoint-350 both:700:checkpoint-700 both:1050:checkpoint-1050
    both:1400:checkpoint-1400 both:1750:
)

adapter_path() {
    printf '%s/qwen3vl_4b_%s%s\n' "$checkpoint_root" "$1" "${2:+/$2}"
}

# Check every requested adapter before committing GPU time.
missing=0
for target in "${targets[@]}"; do
    IFS=: read -r model step subdir <<< "$target"
    [[ $model == base ]] && continue
    adapter=$(adapter_path "$model" "$subdir")
    if [[ ! -f "$adapter/adapter_config.json" ]] ||
       [[ ! -f "$adapter/adapter_model.safetensors" && ! -f "$adapter/adapter_model.bin" ]]; then
        printf 'Missing LoRA config or weights: %s (step %s)\n' "$adapter" "$step" >&2
        missing=1
    fi
done
(( missing == 0 )) || exit 1

mkdir -p "$run_root" "$merge_root"
exec 9>"$run_root/.lock"
flock -n 9 || { printf 'A sweep is already running in %s\n' "$run_root" >&2; exit 1; }

merged_dir=""
cleanup_merge() {
    if [[ -n "$merged_dir" ]]; then
        rm -rf -- "$merged_dir"
        merged_dir=""
    fi
}
trap cleanup_merge EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

record_result() {
    "$python_bin" - "$summary" "$@" <<'PY'
import csv
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

summary, model, step, variant, output_dir = sys.argv[1:]
summary = Path(summary)
output_dir = Path(output_dir)
predictions = output_dir / "predictions.jsonl"
try:
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    subjects = metrics["subjects"]
    sampling = metrics["sampling"]
    if (
        set(subjects) != {"Music", "Chemistry"}
        or any(subjects[subject]["num"] != 30 for subject in subjects)
        or metrics["num_results"] != 60
        or metrics["prompt_variant"] != variant
        or metrics["batch_mode"] != "subject"
        or metrics["gpu_memory_utilization"] != 0.80
        or sampling["seed"] != 3407
        or metrics["image_pixels"] != {"min_pixels": 65536, "max_pixels": 16777216}
    ):
        sys.exit(1)
    with predictions.open(encoding="utf-8") as handle:
        ids = {json.loads(line)["id"] for line in handle}
    if len(ids) != 60:
        sys.exit(1)
except (FileNotFoundError, KeyError, TypeError, ValueError):
    sys.exit(1)

columns = ["model", "step", "prompt_variant", "total_acc", "music_acc", "chem_acc", "output_file"]
row = {
    "model": model,
    "step": step,
    "prompt_variant": variant,
    "total_acc": f"{metrics['overall_accuracy']:.6f}",
    "music_acc": f"{subjects['Music']['accuracy']:.6f}",
    "chem_acc": f"{subjects['Chemistry']['accuracy']:.6f}",
    "output_file": str(predictions),
}
rows = []
if summary.exists():
    with summary.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
key = (model, step, variant)
for index, existing in enumerate(rows):
    if tuple(existing[column] for column in columns[:3]) == key:
        rows[index] = row
        break
else:
    rows.append(row)

with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=summary.parent, delete=False) as handle:
    writer = csv.DictWriter(handle, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    staged = handle.name
os.replace(staged, summary)
PY
}

merge_adapter() {
    "$python_bin" -u - "$base_model" "$1" "$2" <<'PY'
from pathlib import Path
import sys

import torch
from peft import PeftModel
from transformers import AutoModelForImageTextToText, AutoProcessor

sys.path.insert(0, "code")
from run_mmmu import MODEL_REVISION

base_model, adapter_path, output_dir = sys.argv[1:]
revision = None if Path(base_model).is_dir() else MODEL_REVISION
base = AutoModelForImageTextToText.from_pretrained(base_model, revision=revision, dtype=torch.bfloat16)
merged = PeftModel.from_pretrained(base, adapter_path).merge_and_unload(safe_merge=True)
merged.save_pretrained(output_dir, safe_serialization=True)
AutoProcessor.from_pretrained(base_model, revision=revision).save_pretrained(output_dir)
(Path(output_dir) / "MERGED_FROM.txt").write_text(
    f"base={base_model}@{MODEL_REVISION}\nadapter={Path(adapter_path).resolve()}\n",
    encoding="utf-8",
)
PY
}

for target in "${targets[@]}"; do
    IFS=: read -r model step subdir <<< "$target"
    model_path="$base_model"
    for variant in "${variants[@]}"; do
        result_dir="$run_root/$model/step-$step/$variant"
        if record_result "$model" "$step" "$variant" "$result_dir"; then
            printf 'Reusing %s step %s (%s)\n' "$model" "$step" "$variant"
            continue
        fi

        if [[ $model != base && -z "$merged_dir" && "$model_path" == "$base_model" ]]; then
            existing_merged="/shared_dir/merged_models/qwen3vl_4b_${model}"
            if [[ -z "$subdir" && -f "$existing_merged/config.json" ]]; then
                printf 'Using existing merged model: %s\n' "$existing_merged"
                model_path="$existing_merged"
            else
                merged_dir=$(mktemp -d "$merge_root/$model-$step.XXXXXXXX")
                printf 'Merging %s step %s into %s\n' "$model" "$step" "$merged_dir"
                merge_adapter "$(adapter_path "$model" "$subdir")" "$merged_dir"
                model_path="$merged_dir"
            fi
        fi

        printf 'Evaluating %s step %s (%s)\n' "$model" "$step" "$variant"
        "$python_bin" -u code/run_mmmu.py \
            --model_path "$model_path" --data_root "$data_root" --run_dir "$result_dir" \
            --subjects Music,Chemistry --batch_mode subject --seed 3407 \
            --gpu_memory_utilization 0.80 --prompt_variant "$variant" \
            --min_pixels auto --max_pixels auto
        if ! record_result "$model" "$step" "$variant" "$result_dir"; then
            printf 'Evaluation returned but its results failed validation: %s\n' "$result_dir" >&2
            exit 1
        fi
    done
    cleanup_merge
done

printf 'Summary: %s\n' "$summary"
