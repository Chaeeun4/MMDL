#!/usr/bin/env bash
set +x
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

eval_root="${MMMU_CONTROLLED_OUT:-runs/controlled_legacy_cot}"
python_bin="${OVERLAP_PYTHON:-$PWD/.venv-overlap/bin/python}"
lock="$eval_root/.queue.lock"
full="$eval_root/900q/context-32768/seed-3407"
webhook="${DISCORD_WEBHOOK_URL:-${WEBHOOK_URL:-}}"
if [[ -z $webhook && -n ${DISCORD_WEBHOOK_FILE:-} && -r $DISCORD_WEBHOOK_FILE ]]; then
    webhook=$(<"$DISCORD_WEBHOOK_FILE")
fi
if [[ -z $webhook && -f scripts/queue_mmmu_controlled.sh ]]; then
    # Read the existing URL as text. Sourcing the evaluation script would launch its queue.
    webhook=$(sed -nE "s@.*'(https://discord(app)?[.]com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+)'.*@\1@p" \
        scripts/queue_mmmu_controlled.sh)
fi
unset DISCORD_WEBHOOK_URL WEBHOOK_URL

notify() {
    local event="$1" message="$2" payload
    if [[ ! $webhook =~ ^https://(discord\.com|discordapp\.com)/api/webhooks/[0-9]+/[A-Za-z0-9_-]+$ ]]; then
        printf 'Discord %s notification skipped: webhook missing or invalid.\n' "$event" >&2
        return 0
    fi
    if ! payload=$(printf '%s' "$message" | python3 -c '
import json, re, sys
message = re.sub(r"https?://\S+", "[URL redacted]", sys.stdin.read())
print(json.dumps({"content": message[:1900], "allowed_mentions": {"parse": []}}))
'); then
        printf 'Could not build Discord %s notification.\n' "$event" >&2
        return 0
    fi
    if ! printf 'url = "%s"\n' "$webhook" | curl --disable --config - \
        --fail --silent --connect-timeout 5 --max-time 15 --output /dev/null \
        --header 'Content-Type: application/json' --data-binary "$payload"; then
        printf 'Discord %s notification failed.\n' "$event" >&2
    fi
}

stage="preflight"
detail=""
error_log=""
scan_started=0
on_exit() {
    local status="$1" excerpt elapsed
    if (( status != 0 )); then
        excerpt="$detail"
        if [[ -z $excerpt && -n $error_log && -s $error_log ]]; then
            excerpt=$(tail -n 12 "$error_log" | tail -c 1450)
        fi
        notify error "MMMU overlap 오류 · $stage · 종료 코드 $status"$'\n'"${excerpt:-자세한 내용은 overlap_queue.log를 확인하세요.}"
    else
        elapsed=$((SECONDS - scan_started))
        notify finish "MMMU overlap 완료 · ${elapsed}초 · candidates.csv, matches.csv, summary.json 저장 완료"
    fi
    if [[ -n $error_log ]]; then rm -f -- "$error_log"; fi
}
trap 'on_exit $?' EXIT
trap 'detail="중복 검사 작업이 중단됐습니다."; exit 130' INT
trap 'detail="중복 검사 작업이 종료 신호를 받았습니다."; exit 143' TERM

fail() {
    detail="$1"
    printf '%s\n' "$detail" >&2
    exit 1
}

[[ -f "$lock" ]] || fail "Cannot find the existing evaluation queue lock: $lock"
[[ -x "$python_bin" ]] || fail "Cannot run $python_bin. Set OVERLAP_PYTHON to the overlap environment Python."
error_log=$(mktemp)

# The evaluation queue holds this same lock for every mode, including full.
stage="waiting for evaluation"
exec 9<>"$lock"
printf '[%s] Waiting for the evaluation queue to release %s\n' "$(date -Is)" "$lock"
flock 9

stage="checking 900q results"
"$python_bin" - "$full" 2>&1 <<'PY' | tee "$error_log"
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

stage="overlap scan"
scan_started=$SECONDS
printf '[%s] Both 900q results are present. Starting overlap scan on CUDA.\n' "$(date -Is)"
notify start "MMMU overlap 시작 · Base와 PrIMuS 900문항 평가 완료 · CUDA에서 원본 데이터 전수 검사"
"$python_bin" -u experiments/targeted_sft/check_overlap.py --all-raw "$@" --siglip-device cuda \
    2>&1 | tee "$error_log"
