#!/usr/bin/env bash
# Full MMMU-val (900, official prompt) for the step-240 adapters of cm_ft and c2cm_ft.
# Waits for the MMMU-Pro queue, then merge -> eval -> compare, one run at a time. Rerun to resume.
#   setsid nohup bash scripts/run_step240_eval.sh > /data/$USER/rft/step240_eval.log 2>&1 < /dev/null &
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /data/$USER/env.sh
STEP="${STEP:-240}"
ARMS="${ARMS:-cm c2cm}"
OUT="/data/$USER/rft/step${STEP}"; mkdir -p "$OUT"
log() { echo "[$(date '+%F %T')] $*"; }

while pgrep -u "$USER" -f "scripts/run_pro_eval.sh" > /dev/null; do sleep 300; done
for a in $ARMS; do
  run="${a}_step${STEP}_full"
  adapter="/data/$USER/ckpt/${a}_ft/adapter_step${STEP}"
  merged="/data/$USER/ckpt/${a}_ft_step${STEP}_merged"
  if [[ ! -f "runs/$run/metrics.json" ]]; then
    if [[ ! -f "$merged/MERGED_FROM.txt" ]]; then
      rm -rf "$merged"; log "merge $adapter"
      python code/merge_lora.py --adapter "$adapter" --out "$merged"
    fi
    for i in $(seq 1 288); do  # shared server: wait for a free GPU
      used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
      (( used < 1000 )) && break; (( i % 12 == 1 )) && log "GPU busy (${used} MiB) - waiting"; sleep 300
    done
    resume=(); [[ -d "runs/$run/per_subject" ]] && resume=(--resume)
    log "eval $run"
    MODEL_PATH="$merged" DATA_ROOT="$HF_HOME" bash scripts/run_baseline_modelcard.sh --fg --run_name "$run" \
        "${resume[@]}" -- --prompt_variant official || log "$run exited non-zero"
    sleep 5; pkill -u "$USER" -f "Engine[C]ore" 2>/dev/null || true; sleep 10
  fi
  [[ -f "runs/$run/metrics.json" ]] || continue
  rm -rf "$merged"
  final="runs/${a}_final_full"; [[ "$a" == cm ]] && final="runs/cm_final_official"
  python code/compare_runs.py --baseline runs/baseline_modelcard_v1 "$final" "runs/$run" --out "$OUT/compare_${a}.md" || true
  python code/compare_runs.py --baseline "$final" "runs/$run" --out "$OUT/compare_${a}_vs_final.md" || true
done
log "step${STEP} eval done"
