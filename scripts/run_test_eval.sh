#!/usr/bin/env bash
# MMMU test (10,500 questions, pinned revision, evaluation only) with the official prompt, one GPU.
# The 30 subjects are split into groups (smallest subjects first) and the models take turns per group,
# so a paired comparison on the finished subjects exists long before the whole test set is done.
# Runs land in runs/test_<model>; finished subjects are skipped, so rerun the same command to resume.
#   setsid nohup bash scripts/run_test_eval.sh > /data/$USER/rft/test_eval.log 2>&1 < /dev/null &
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /data/$USER/env.sh
MODELS="${MODELS:-base offc1b}"
OUT="/data/$USER/rft/test_eval"; mkdir -p "$OUT"
GROUPS_=(
  "Literature,Diagnostics_and_Laboratory_Medicine,Design,Marketing,Art"
  "Manage,Sociology,Electronics,Economics,History"
  "Agriculture,Psychology,Clinical_Medicine,Basic_Medical_Science,Music"
  "Biology,Finance,Computer_Science,Accounting,Physics"
  "Mechanical_Engineering,Art_Theory,Pharmacy,Energy_and_Power,Materials"
  "Math,Public_Health,Architecture_and_Engineering,Geography,Chemistry"
)
log() { echo "[$(date '+%F %T')] $*"; }
model_path() { [[ "$1" == base ]] && echo "Qwen/Qwen3-VL-4B-Instruct" || echo "/data/$USER/ckpt/${1}_ft_merged"; }
wait_gpu() {
  for i in $(seq 1 288); do  # shared server: wait for a free GPU
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
    (( used < 1000 )) && return 0; (( i % 12 == 1 )) && log "GPU busy (${used} MiB) - waiting"; sleep 300
  done
}
done_all() {  # every subject of the group has a per-subject checkpoint
  local run="$1" s; IFS=',' read -ra subs <<< "$2"
  for s in "${subs[@]}"; do [[ -f "runs/$run/per_subject/$s.jsonl" ]] || return 1; done
}
eval_run() {  # eval_run <model> <extra run_mmmu args...>
  local m="$1"; shift; local run="test_$m"
  wait_gpu
  resume=(); [[ -d "runs/$run/per_subject" ]] && resume=(--resume)
  MODEL_PATH="$(model_path "$m")" DATA_ROOT="$HF_HOME" bash scripts/run_baseline_modelcard.sh --fg --run_name "$run" \
      "${resume[@]}" -- --benchmark mmmu_test --prompt_variant official "$@" || log "$run exited non-zero"
  sleep 5; pkill -u "$USER" -f "Engine[C]ore" 2>/dev/null || true; sleep 10
}
compare() {
  local first="${MODELS%% *}" rest=()
  for m in ${MODELS#* }; do [[ "$m" != "$first" && -d "runs/test_$m/per_subject" ]] && rest+=("runs/test_$m"); done
  [[ ${#rest[@]} -gt 0 ]] && python code/compare_runs.py --baseline "runs/test_$first" "${rest[@]}" --out "$OUT/compare.md" || true
}

for g in "${GROUPS_[@]}"; do
  for m in $MODELS; do
    done_all "test_$m" "$g" && { log "test_$m [$g] already done"; continue; }
    log "eval test_$m [$g]"
    eval_run "$m" --subjects "$g"
  done
  compare
done
for m in $MODELS; do  # final pass over all 30 subjects: nothing left to generate, writes the full metrics/summary
  [[ -f "runs/test_$m/FULL_DONE" ]] && continue
  log "final scoring test_$m"
  eval_run "$m"
  grep -q '"num_results": 10500' "runs/test_$m/metrics.json" && touch "runs/test_$m/FULL_DONE"
done
compare
log "test eval done"
