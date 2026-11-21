#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python_bin="${PYTHON_BIN:-python3}"
data_root="${MMMU_CACHE:-${HF_HOME:-/workspace/huggingface_cache}}"
checkpoint_root="${CHECKPOINT_ROOT:-/shared_dir/outputs}"
merge_root="${MERGE_ROOT:-/shared_dir/tmp_merged}"
run_root="runs/sweep_60q_both_rerun"
summary="$run_root/summary_bothrerun.csv"
base_model="${BASE_MODEL_PATH:-Qwen/Qwen3-VL-4B-Instruct}"
model="both_rerun"
both_dir="$checkpoint_root/qwen3vl_4b_${model}"
variants=(official legacy_cot describe_cot)

if [[ -n "${BASE_MODEL_PATH:-}" ]]; then
    if [[ ! -f "$base_model/config.json" ]]; then
        printf 'BASE_MODEL_PATH must point to a downloaded model snapshot: %s\n' "$base_model" >&2
        exit 1
    fi
    base_model=$(realpath -- "$base_model")
fi

export VLLM_WORKER_MULTIPROC_METHOD="${VLLM_WORKER_MULTIPROC_METHOD:-spawn}"

# 각 줄은 step:adapter 하위 경로. 하위 경로가 비어 있으면 최종 어댑터.
target_list=$("$python_bin" - "$both_dir" <<'PY'
import json
import sys
from pathlib import Path

run = Path(sys.argv[1])


def has_adapter(path):
    return (path / "adapter_config.json").is_file() and any(
        (path / name).is_file()
        for name in ("adapter_model.safetensors", "adapter_model.bin")
    )


if not has_adapter(run):
    sys.exit(f"최종 LoRA 어댑터를 찾을 수 없음: {run}")

final_step = None
state_path = run / "trainer_state.json"
log_path = run / "trainer_log.jsonl"

if state_path.is_file():
    state = json.loads(state_path.read_text(encoding="utf-8"))
    final_step = state.get("global_step")

if not isinstance(final_step, int) or final_step <= 0:
    if log_path.is_file():
        with log_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entry = json.loads(line)
                step = entry.get("current_steps")
                if isinstance(step, int) and step > 0 and step == entry.get("total_steps"):
                    final_step = step

if not isinstance(final_step, int) or final_step <= 0:
    sys.exit(f"최종 학습 step을 확인할 수 없음: {run}")

saved_steps = []
for path in run.glob("checkpoint-*"):
    suffix = path.name.removeprefix("checkpoint-")
    if not suffix.isdecimal() or not has_adapter(path):
        continue
    step = int(suffix)
    if 0 < step < final_step:
        saved_steps.append(step)

if not saved_steps:
    sys.exit(f"사용 가능한 중간 체크포인트가 없음: {run}")

selected = set()
for percent in (20, 40, 60, 80):
    step = min(saved_steps, key=lambda value: (abs(value * 100 - final_step * percent), value))
    print(f"{percent}% → checkpoint-{step}", file=sys.stderr)
    selected.add(step)

for step in sorted(selected):
    print(f"{step}:checkpoint-{step}")

print(f"100% → final adapter (step {final_step})", file=sys.stderr)
print(f"{final_step}:")
PY
)
mapfile -t targets <<< "$target_list"

mkdir -p "$run_root" "$merge_root"
exec 9>"$run_root/.lock"
flock -n 9 || {
    printf 'A sweep is already running in %s\n' "$run_root" >&2
    exit 1
}

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
import sys
from pathlib import Path
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

with NamedTemporaryFile(
    mode="w", encoding="utf-8", newline="", dir=summary.parent, delete=False
) as handle:
    writer = csv.DictWriter(handle, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    staged = handle.name

os.replace(staged, summary)
PY
}

merge_adapter() {
    "$python_bin" -u - "$base_model" "$1" "$2" <<'PY'
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForImageTextToText, AutoProcessor

sys.path.insert(0, "code")
from run_mmmu import MODEL_REVISION

base_model, adapter_path, output_dir = sys.argv[1:]
revision = None if Path(base_model).is_dir() else MODEL_REVISION

base = AutoModelForImageTextToText.from_pretrained(
    base_model, revision=revision, dtype=torch.bfloat16
)
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
    IFS=: read -r step subdir <<< "$target"
    adapter="$both_dir${subdir:+/$subdir}"

    for variant in "${variants[@]}"; do
        result_dir="$run_root/$model/step-$step/$variant"

        if record_result "$model" "$step" "$variant" "$result_dir"; then
            printf 'Reusing %s step %s (%s)\n' "$model" "$step" "$variant"
            continue
        fi

        if [[ -z "$merged_dir" ]]; then
            merged_dir=$(mktemp -d "$merge_root/$model-$step.XXXXXXXX")
            printf 'Merging %s into %s\n' "$adapter" "$merged_dir"
            merge_adapter "$adapter" "$merged_dir"
        fi

        printf 'Evaluating %s step %s (%s)\n' "$model" "$step" "$variant"
        "$python_bin" -u code/run_mmmu.py \
            --model_path "$merged_dir" \
            --data_root "$data_root" \
            --run_dir "$result_dir" \
            --subjects Music,Chemistry \
            --batch_mode subject \
            --seed 3407 \
            --gpu_memory_utilization 0.80 \
            --prompt_variant "$variant" \
            --min_pixels auto --max_pixels auto

        if ! record_result "$model" "$step" "$variant" "$result_dir"; then
            printf 'Evaluation returned but its results failed validation: %s\n' "$result_dir" >&2
            exit 1
        fi
    done

    cleanup_merge
done

printf 'Summary: %s\n' "$summary"
