#!/usr/bin/env bash
# C1 (format) via rejection-sampling fine-tuning, one GPU, one job at a time:
#   generate (4 prompt strategies of the base model on ViRL39K, MMMU-overlap removed)
#   -> select -> LoRA SFT -> merge -> MMMU-val 900 eval with describe_cot
#   -> base model 900 eval with the same describe_cot prompt (the fair reference)
# Every step is skipped if its output already exists, so rerunning resumes.
#
#   setsid nohup bash scripts/run_c1_rft.sh > /data/$USER/rft/c1/queue.log 2>&1 < /dev/null &
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
source /data/$USER/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn TOKENIZERS_PARALLELISM=false

NAME="${NAME:-c1}"
NQ="${NQ:-6000}"
WORK="/data/$USER/rft/$NAME"
CKPT="/data/$USER/ckpt/${NAME}_rft"
POOL="/data/$USER/train_data/ViRL39K"
mkdir -p "$WORK"
log() { echo "[$(date '+%F %T')] $*"; }
gpu_clear() {  # never start a job on top of a leftover engine
  local used; used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  if (( used > 1000 )); then log "GPU busy (${used} MiB used) - stopping"; nvidia-smi; exit 1; fi
}

if [[ ! -f "$WORK/gen.done" ]]; then
  gpu_clear; log "generate: $NQ questions x 4 agents"
  python code/gen_rft.py generate --pool "$POOL" --n_questions "$NQ" --chunk 1024 --out "$WORK/gen.jsonl"
  touch "$WORK/gen.done"
fi

log "select"
python code/gen_rft.py select --gen "$WORK/gen.jsonl" --out_dir "$WORK"

if [[ ! -f "$CKPT/adapter/adapter_config.json" ]]; then
  gpu_clear; log "train LoRA"
  python code/train_lora.py --train_jsonl "$WORK/sft.jsonl" --out_dir "$CKPT" --epochs 1 \
      --grad_accum 16 --lr 1e-4 --rank 16 --target language
fi

if [[ ! -f "${CKPT}_merged/model.safetensors" ]]; then
  log "merge"
  python code/merge_lora.py --adapter "$CKPT/adapter" --out "${CKPT}_merged"
fi

run_eval() {  # $1 run name, $2 model path
  if [[ -f "runs/$1/metrics.json" ]]; then log "eval $1 already done"; return; fi
  gpu_clear; log "eval $1 ($2)"
  MODEL_PATH="$2" DATA_ROOT="$HF_HOME" bash scripts/run_baseline_modelcard.sh --fg --run_name "$1" \
      -- --prompt_variant describe_cot || log "eval $1 exited non-zero"
}
run_eval "${NAME}_rft_describe" "${CKPT}_merged"
run_eval "base_describe" "Qwen/Qwen3-VL-4B-Instruct"

log "compare"
python code/compare_runs.py --baseline runs/base_describe runs/${NAME}_rft_describe --out "$WORK/compare.md" || true
python code/compare_runs.py --baseline runs/baseline_modelcard_v1 --noise runs/p1_noise_seed1234 \
  runs/base_describe runs/${NAME}_rft_describe --out "$WORK/compare_vs_official.md" || true
log "queue done"
