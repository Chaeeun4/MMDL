#!/usr/bin/env bash
# MMMU-Pro (test 1,730; evaluation only) with the official prompt, one GPU, one run at a time.
# Runs land in runs/pro_<setting>_<model>; finished runs are skipped, unfinished ones resume.
#   MODELS="base offc1b" SETTINGS="standard10 vision" \
#     setsid nohup bash scripts/run_pro_eval.sh > /data/$USER/rft/pro_eval.log 2>&1 < /dev/null &
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /data/$USER/env.sh
MODELS="${MODELS:-base offc1b}"
SETTINGS="${SETTINGS:-standard10 vision}"
log() { echo "[$(date '+%F %T')] $*"; }
for s in $SETTINGS; do for m in $MODELS; do
  run="pro_${s}_${m}"
  [[ -f "runs/$run/metrics.json" ]] && { log "$run already done"; continue; }
  path="Qwen/Qwen3-VL-4B-Instruct"; [[ "$m" != base ]] && path="/data/$USER/ckpt/${m}_ft_merged"
  for i in $(seq 1 288); do  # shared server: wait for a free GPU
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
    (( used < 1000 )) && break; (( i % 12 == 1 )) && log "GPU busy (${used} MiB) - waiting"; sleep 300
  done
  resume=(); [[ -d "runs/$run/per_subject" ]] && resume=(--resume)
  log "eval $run ($path)"
  MODEL_PATH="$path" DATA_ROOT="$HF_HOME" bash scripts/run_baseline_modelcard.sh --fg --run_name "$run" \
      "${resume[@]}" -- --benchmark "pro_$s" || log "$run exited non-zero"
  sleep 5; pkill -u "$USER" -f "EngineCore" 2>/dev/null || true; sleep 10
  grep -E "^Overall" "runs/$run/run.log" | tail -1 || true
done; done
log "pro eval done"
