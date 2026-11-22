#!/usr/bin/env bash
# Round 2 of the official-prompt self-RFT (arm "offr2"), one GPU, one job at a time:
#   generate : the round-1 model (offc1b, merged) answers NEW ViRL39K questions (not used in round 1,
#              MMMU-overlap removed) with the official MMMU prompt, $SAMPLES samples per question
#   select   : keep correct, cleanly finished solutions of 80..800 tokens; questions that every sample got
#              right are mostly dropped (difficulty-based selection, cf. ThinkLite-VL arXiv 2504.07934);
#              iterating on the model's own solutions follows OpenVLThinker (arXiv 2503.17352)
#   build    : round-1 data (c1b) + round-2 data under the official prompt, images dHash-checked against MMMU
#   train    : LoRA SFT from the BASE model on the union -> merge -> MMMU-val 900 with the official prompt
# MMMU / MMMU-Pro are used for evaluation only. Rerun the same command to resume.
#
#   mkdir -p /data/$USER/rft/r2 && setsid nohup bash scripts/run_r2.sh > /data/$USER/rft/r2/queue.log 2>&1 < /dev/null &
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /data/$USER/env.sh
export VLLM_WORKER_MULTIPROC_METHOD=spawn TOKENIZERS_PARALLELISM=false
D="/data/$USER"
NQ="${NQ:-8000}"
SAMPLES="${SAMPLES:-4}"
GEN_MODEL="${GEN_MODEL:-$D/ckpt/offc1b_ft_merged}"
W="$D/rft/r2"
ARM="${ARM:-offr2}"
STOP_AFTER="${STOP_AFTER:-}"          # generate | build : stop there (e.g. to inspect the data first)
mkdir -p "$W"
log() { echo "[$(date '+%F %T')] $*"; }

if [[ ! -f "$W/gen.done" ]]; then
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  if (( used > 1000 )); then log "GPU busy (${used} MiB used) - stopping"; exit 1; fi
  log "generate: $NQ new questions x $SAMPLES samples with $GEN_MODEL"
  python code/gen_rft.py generate --pool "$D/train_data/ViRL39K" --n_questions "$NQ" --agents official \
      --samples "$SAMPLES" --model_path "$GEN_MODEL" --exclude_gen "$D/rft/c1/gen.jsonl" \
      --max_tokens 1024 --chunk 512 --out "$W/gen.jsonl"   # select keeps <= 800 tokens; longer ones are mostly loops
  touch "$W/gen.done"
  sleep 5; pkill -u "$USER" -f "EngineCore" 2>/dev/null || true; sleep 10
fi
[[ "$STOP_AFTER" == generate ]] && { log "stop after generate"; exit 0; }

log "select"
python code/gen_rft.py select --gen "$W/gen.jsonl" --out_dir "$W" --pick random --per_question 1 \
    --max_tokens 800 --min_tokens 80 --drop_blank

if [[ ! -f "$D/rft/$ARM/build_stats.json" ]]; then
  log "build $ARM"
  python code/build_official_sft.py --from_sft "$D/rft/c1b/sft.jsonl" "$W/sft.jsonl" --check_images \
      --out_dir "$D/rft/$ARM"
fi
[[ "$STOP_AFTER" == build ]] && { log "stop after build"; exit 0; }

NAME="$ARM" PROMPT=official BASELINE=runs/baseline_modelcard_v1 CKPT_EVAL=0 SAVE_EVERY=200 \
    bash scripts/run_cm_ft.sh || log "$ARM failed"
python code/compare_runs.py --baseline runs/offc1b_final_full "runs/${ARM}_final_full" \
    --out "$D/rft/$ARM/compare_vs_offc1b.md" || true
log "r2 queue done"
