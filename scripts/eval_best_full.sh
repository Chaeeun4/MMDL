#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python_bin="${PYTHON_BIN:-python3}"
checkpoint_root="${CHECKPOINT_ROOT:-/shared_dir/outputs}"
merge_root="${MERGE_ROOT:-/shared_dir/tmp_merged}"
base_model="${BASE_MODEL_PATH:-Qwen/Qwen3-VL-4B-Instruct}"
data_root="${MMMU_CACHE:-${HF_HOME:-/workspace/huggingface_cache}}"
rerun_root="runs/sweep_60q_both_rerun"

# 실행 중인 both_rerun sweep과 같은 잠금을 사용한다.
printf 'Waiting for both_rerun sweep to release its lock...\n'
exec 9>"$rerun_root/.lock"
flock 9

winner=$("$python_bin" - "$checkpoint_root" "$rerun_root" <<'PY'
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

checkpoint_root = Path(sys.argv[1])
rerun_root = Path(sys.argv[2])
both_dir = checkpoint_root / "qwen3vl_4b_both_rerun"
variants = {"official", "legacy_cot", "describe_cot"}

state_path = both_dir / "trainer_state.json"
if state_path.is_file():
    final_step = int(json.loads(state_path.read_text())["global_step"])
else:
    final_step = None
    with (both_dir / "trainer_log.jsonl").open() as handle:
        for line in handle:
            if line.strip():
                entry = json.loads(line)
                step = entry.get("current_steps")
                if step and step == entry.get("total_steps"):
                    final_step = int(step)
    if final_step is None:
        sys.exit("both_rerun의 최종 학습 step을 확인할 수 없습니다.")

sources = [
    (Path("runs/sweep_60q/summary.csv"), {"primus_only", "pubchem_only"}),
    (rerun_root / "summary_bothrerun.csv", {"both_rerun"}),
]

rows = []
for path, models in sources:
    with path.open(newline="", encoding="utf-8") as handle:
        rows.extend(row for row in csv.DictReader(handle) if row["model"] in models)

final_variants = {
    row["prompt_variant"]
    for row in rows
    if row["model"] == "both_rerun" and int(row["step"]) == final_step
}
if final_variants != variants:
    sys.exit("both_rerun 최종 체크포인트의 세 프롬프트 평가가 아직 완료되지 않았습니다.")

# 동률이면 모델명, step, 프롬프트 순으로 한 조합을 고른다.
ranked = sorted(rows, key=lambda row: (
    -Decimal(row["total_acc"]),
    row["model"],
    int(row["step"]),
    row["prompt_variant"],
))
best = ranked[0]
if len(ranked) > 1 and Decimal(ranked[1]["total_acc"]) == Decimal(best["total_acc"]):
    print("60문항 정확도 공동 1위가 있어 동률 규칙을 적용합니다.", file=sys.stderr)

model = best["model"]
step = int(best["step"])
adapter = checkpoint_root / f"qwen3vl_4b_{model}"
final_steps = {"primus_only": 500, "pubchem_only": 1188, "both_rerun": final_step}
if step != final_steps[model]:
    adapter = adapter / f"checkpoint-{step}"

if not (adapter / "adapter_config.json").is_file() or not any(
    (adapter / name).is_file()
    for name in ("adapter_model.safetensors", "adapter_model.bin")
):
    sys.exit(f"선택된 어댑터의 파일을 찾을 수 없습니다: {adapter}")

print(model, step, best["prompt_variant"], best["total_acc"], adapter, sep="\t")
PY
)

IFS=$'\t' read -r model step variant accuracy adapter <<< "$winner"
printf 'Winner: %s / step %s / %s / 60q accuracy %s\n' \
    "$model" "$step" "$variant" "$accuracy"

mkdir -p "$merge_root"
merged_dir=$(mktemp -d "$merge_root/full-best.XXXXXXXX")
trap 'rm -rf -- "$merged_dir"' EXIT
export VLLM_WORKER_MULTIPROC_METHOD="${VLLM_WORKER_MULTIPROC_METHOD:-spawn}"

"$python_bin" -u - "$base_model" "$adapter" "$merged_dir" <<'PY'
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForImageTextToText, AutoProcessor

sys.path.insert(0, "code")
from run_mmmu import MODEL_REVISION

base_model, adapter, output = sys.argv[1:]
revision = None if Path(base_model).is_dir() else MODEL_REVISION
base = AutoModelForImageTextToText.from_pretrained(
    base_model, revision=revision, dtype=torch.bfloat16
)
merged = PeftModel.from_pretrained(base, adapter).merge_and_unload(safe_merge=True)
merged.save_pretrained(output, safe_serialization=True)
AutoProcessor.from_pretrained(base_model, revision=revision).save_pretrained(output)
PY

result_dir="runs/full_eval/$model/step-$step/$variant"

"$python_bin" -u code/run_mmmu.py \
    --model_path "$merged_dir" \
    --data_root "$data_root" \
    --run_dir "$result_dir" \
    --batch_mode subject \
    --seed 3407 \
    --gpu_memory_utilization 0.80 \
    --prompt_variant "$variant" \
    --min_pixels auto --max_pixels auto

"$python_bin" - "$result_dir/metrics.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
metrics = json.loads(path.read_text())
if metrics["num_results"] != 900:
    sys.exit(f"예상한 900문항과 다릅니다: {metrics['num_results']}")
print(f"MMMU 900문항 전체 정확도: {metrics['overall_accuracy']:.2%}")
print(f"Metrics: {path}")
PY
