#!/usr/bin/env bash
# Two checks the offc1b claim still needs, one GPU, one job at a time. Rerun the same command to resume.
#   1) c1b_final_official : the C1b model (same solutions, trained with the describe_cot wording) evaluated with the
#      OFFICIAL prompt -> the missing control for "matching the training format to the eval prompt is what helped".
#   2) offc1bs1           : offc1b retrained with another training seed (same data) -> does 595/900 reproduce?
# Waits for scripts/run_step240_eval.sh to exit and for a free GPU before starting.
#   setsid nohup bash scripts/run_presentation_checks.sh > /data/$USER/rft/presentation_checks.log 2>&1 < /dev/null &
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /data/$USER/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn TOKENIZERS_PARALLELISM=false
D="/data/$USER"; OUT="$D/rft/presentation_checks"; mkdir -p "$OUT"
STEPS="${STEPS:-c1b_official seed}"
SEED="${SEED:-1}"
log() { echo "[$(date '+%F %T')] $*"; }

while pgrep -u "$USER" -f "scripts/run_step240_eval.sh" > /dev/null; do sleep 120; done

for s in $STEPS; do
  case "$s" in
    c1b_official)
      run="c1b_final_official"; merged="$D/ckpt/c1b_rft_merged"
      if [[ ! -f "runs/$run/metrics.json" ]]; then
        [[ -f "$merged/MERGED_FROM.txt" ]] || { log "missing $merged"; exit 1; }
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
      python code/compare_runs.py --baseline runs/baseline_modelcard_v1 "runs/$run" runs/offc1b_final_full --out "$OUT/c1b_official_vs_base.md" || true
      python code/compare_runs.py --baseline "runs/$run" runs/offc1b_final_full --out "$OUT/offc1b_vs_c1b_official.md" || true
      ;;
    seed)
      name="offc1bs${SEED}"; W="$D/rft/$name"; mkdir -p "$W"
      for f in train.jsonl val.jsonl build_stats.json; do [[ -f "$W/$f" ]] || cp "$D/rft/offc1b/$f" "$W/$f"; done
      NAME="$name" PROMPT=official BASELINE=runs/baseline_modelcard_v1 CKPT_EVAL=0 SAVE_EVERY=200 \
          TRAIN_ARGS="--seed $SEED" bash scripts/run_cm_ft.sh || log "$name failed"
      [[ -f "runs/${name}_final_full/metrics.json" ]] || continue
      python code/compare_runs.py --baseline runs/offc1b_final_full "runs/${name}_final_full" --out "$OUT/${name}_vs_offc1b.md" || true
      ;;
    *) log "unknown step $s"; exit 1 ;;
  esac
done
log "presentation checks done"
