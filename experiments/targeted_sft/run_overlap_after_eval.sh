#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

eval_root="${MMMU_CONTROLLED_OUT:-runs/controlled_legacy_cot}"
python_bin="${OVERLAP_PYTHON:-$PWD/.venv-overlap/bin/python}"
lock="$eval_root/.queue.lock"
full="$eval_root/900q/context-32768/seed-3407"

if [[ ! -f "$lock" ]]; then
    printf 'Cannot find the existing evaluation queue lock: %s\n' "$lock" >&2
    exit 1
fi
if [[ ! -x "$python_bin" ]]; then
    printf 'Cannot run %s. Set OVERLAP_PYTHON to the overlap environment Python.\n' "$python_bin" >&2
    exit 1
fi

# The evaluation queue holds this same lock for every mode, including full.
exec 9<>"$lock"
printf '[%s] Waiting for the evaluation queue to release %s\n' "$(date -Is)" "$lock"
flock 9

"$python_bin" - "$full" <<'PY'
import json
from pathlib import Path
import sys

full = Path(sys.argv[1])
for model in ("base", "primus_only"):
    run = full / model
    path = run / "metrics.json"
    if not path.is_file() or not (run / "predictions.jsonl").is_file():
        sys.exit(f"900q output missing for {model}: {run}. Overlap scan did not start.")
    if json.loads(path.read_text()).get("num_results") != 900:
        sys.exit(f"900q evaluation incomplete for {model}: {path}. Overlap scan did not start.")
PY

printf '[%s] Both 900q results are present. Starting overlap scan on CUDA.\n' "$(date -Is)"
exec "$python_bin" -u experiments/targeted_sft/check_overlap.py --all-raw "$@" --siglip-device cuda
