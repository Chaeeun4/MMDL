#!/usr/bin/env bash
# Stage 3: chemistry/music mix + teacher-distilled ViRL39K answers, evaluated with the OFFICIAL prompt.
#   wait for / finish the teacher generation (external model = training-data generation only)
#   -> gen_rft select (4B self-generated answers + correct teacher answers)
#   -> scripts/run_cm_ft.sh with that file as the general replay data
# Stages to compare (all official prompt): runs/baseline_modelcard_v1, runs/cm_final_official, runs/c2cm_final_full
#
#   setsid nohup bash scripts/run_c2cm.sh > /data/$USER/rft/c2/queue.log 2>&1 < /dev/null &
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /data/$USER/env.sh
unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN   # talk to the Anthropic API directly
W="/data/$USER/rft/c2"
TEACHER_MODEL="${TEACHER_MODEL:-claude-sonnet-5-5}"
log() { echo "[$(date '+%F %T')] $*"; }

while pgrep -u "$USER" -f "gen_teacher.py.*teacher_claude" > /dev/null; do sleep 30; done
log "teacher: retry pass for failed calls"
python code/gen_teacher.py --ids_file /data/$USER/rft/c1b/no_clean_ids.txt \
    --contamination /data/$USER/train_data/ViRL39K/contamination.json \
    --provider anthropic --model "$TEACHER_MODEL" --workers 8 --out "$W/teacher_claude.jsonl" || log "retry pass failed"

log "select"
python code/gen_rft.py select --gen /data/$USER/rft/c1/gen.jsonl "$W/teacher_claude.jsonl" \
    --out_dir "$W" --pick random --exclude_agents concise

NAME=c2cm BUILD_ARGS="--replay $W/sft.jsonl" PROMPT=official BASELINE=runs/baseline_modelcard_v1 \
    bash scripts/run_cm_ft.sh
