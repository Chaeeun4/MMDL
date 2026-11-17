#!/usr/bin/env bash
# Chemistry + Music fine-tuning queue, one GPU, one job at a time:
#   build data (chem/music QA + original tasks + general replay; MMMU contamination check)
#   -> LoRA SFT with a checkpoint every $SAVE_EVERY steps (resumable)
#   -> every checkpoint: merge -> MMMU-val Chemistry+Music eval (describe_cot) -> report
#   -> final checkpoint: full MMMU-val 900 eval -> compare with runs/base_describe
# Every step is skipped when its output exists, so rerunning the same command resumes.
# MMMU is used for evaluation only; nothing from MMMU / MMMU-Pro is trained on.
#
#   mkdir -p /data/$USER/rft/cm && setsid nohup bash scripts/run_cm_ft.sh > /data/$USER/rft/cm/queue.log 2>&1 < /dev/null &
#   tail -f /data/$USER/rft/cm/queue.log          # progress
#   cat /data/$USER/rft/cm/ckpt_report.md         # checkpoint table (rewritten after every eval)
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
source /data/$USER/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn TOKENIZERS_PARALLELISM=false

NAME="${NAME:-cm}"
SAVE_EVERY="${SAVE_EVERY:-120}"
BUILD_ARGS="${BUILD_ARGS:-}"
TRAIN_ARGS="${TRAIN_ARGS:-}"
EVAL_SUBJECTS="${EVAL_SUBJECTS:-Chemistry,Music}"
FULL_EVAL="${FULL_EVAL:-1}"
CKPT_EVAL="${CKPT_EVAL:-1}"                 # 0 = skip the per-checkpoint subset evals (checkpoints are still saved)
PROMPT="${PROMPT:-describe_cot}"            # official | describe_cot
BASELINE="${BASELINE:-runs/base_describe}"  # base model run with the same prompt
WORK="/data/$USER/rft/$NAME"
CKPT="/data/$USER/ckpt/${NAME}_ft"
mkdir -p "$WORK"
log() { echo "[$(date '+%F %T')] $*"; }
gpu_wait() {  # shared server: wait (up to 24 h) instead of starting on top of another job
  local used i
  for i in $(seq 1 288); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
    if (( used < 1000 )); then return 0; fi
    (( i % 12 == 1 )) && log "GPU busy (${used} MiB used) - waiting"
    sleep 300
  done
  log "GPU still busy after 24 h - stopping"; exit 1
}
engine_cleanup() {  # vLLM can leave an orphaned EngineCore holding the GPU
  sleep 5; pkill -u "$USER" -f "EngineCore" 2>/dev/null || true; sleep 10
}

if [[ ! -f "$WORK/train.jsonl" || ! -f "$WORK/build_stats.json" ]]; then
  log "build data"
  python code/build_cm_data.py --out_dir "$WORK" $BUILD_ARGS
fi

if [[ ! -f "$CKPT/adapter/adapter_config.json" ]]; then
  gpu_wait; log "train LoRA (checkpoint every $SAVE_EVERY steps)"
  python code/train_lora.py --train_jsonl "$WORK/train.jsonl" --val_jsonl "$WORK/val.jsonl" --out_dir "$CKPT" \
      --epochs 1 --grad_accum 16 --lr 1e-4 --rank 16 --target language \
      --save_every "$SAVE_EVERY" --resume $TRAIN_ARGS
fi

report() {
  python code/ckpt_report.py --name "$NAME" --ckpt "$CKPT" --baseline "$BASELINE" --out "$WORK/ckpt_report.md" > /dev/null || true
}
eval_ckpt() {  # $1 adapter dir, $2 run name, $3 extra run_mmmu args, $4 keep merged (0/1)
  local adapter="$1" run="$2" extra="$3" keep="$4" merged="${CKPT}_merged_tmp"
  [[ "$keep" == 1 ]] && merged="${CKPT}_merged"
  if [[ -f "runs/$run/metrics.json" ]]; then log "eval $run already done"; return; fi
  if [[ ! -f "$merged/MERGED_FROM.txt" ]] || ! grep -q "adapter=$adapter\$" "$merged/MERGED_FROM.txt"; then
    rm -rf "$merged"; log "merge $adapter"
    python code/merge_lora.py --adapter "$adapter" --out "$merged"
  fi
  gpu_wait; log "eval $run"
  local resume=(); [[ -d "runs/$run/per_subject" ]] && resume=(--resume)
  MODEL_PATH="$merged" DATA_ROOT="$HF_HOME" bash scripts/run_baseline_modelcard.sh --fg --run_name "$run" \
      "${resume[@]}" -- --prompt_variant "$PROMPT" $extra || log "eval $run exited non-zero"
  engine_cleanup
  [[ "$keep" == 1 ]] || rm -rf "$merged"
  report
}

# intermediate checkpoints, in training order, on the two target subjects
for d in $([[ "$CKPT_EVAL" == 1 ]] && ls -d "$CKPT"/adapter_step* 2>/dev/null | sort -V); do
  eval_ckpt "$d" "${NAME}_$(basename "$d" | sed 's/adapter_//')_cm" "--subjects $EVAL_SUBJECTS" 0
done

# final adapter: all 900 questions (this is the number to compare with base_describe)
if [[ "$FULL_EVAL" == 1 ]]; then
  eval_ckpt "$CKPT/adapter" "${NAME}_final_full" "" 1
  python code/compare_runs.py --baseline "$BASELINE" "runs/${NAME}_final_full" --out "$WORK/compare.md" || true
else
  eval_ckpt "$CKPT/adapter" "${NAME}_stepfinal_cm" "--subjects $EVAL_SUBJECTS" 1
fi
report
log "queue done"
