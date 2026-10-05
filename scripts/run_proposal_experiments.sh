#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Essential experiments for the proposal, run ONE AT A TIME on one GPU.
#
#   source /data/jinagg/env.sh            # venv + LD_LIBRARY_PATH unset
#   bash scripts/run_proposal_experiments.sh            # all, in background
#   bash scripts/run_proposal_experiments.sh p3 p4      # only some
#   bash scripts/run_proposal_experiments.sh --fg all   # foreground
#   bash scripts/run_proposal_experiments.sh --list
#
# Completed runs (metrics.json status=completed) are skipped, so re-running
# the same command resumes the queue. Progress: tail -f runs/proposal_queue.log
# Final table: runs/proposal_table.md (code/compare_runs.py)
# ---------------------------------------------------------------------------
set -uo pipefail
USER="${USER:-$(whoami)}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
GPU="${GPU:-0}"
BASELINE="${BASELINE:-runs/baseline_modelcard_v1}"
SYM="Sheet Music,Chemical Structures,Sketches and Drafts,Technical Blueprints"
CKPT_DIR="${CKPT_DIR:-/data/$USER/ckpt}"

# name | purpose | extra args for run_mmmu.py (via the baseline launcher)
EXPERIMENTS=(
  "p3_sym_cot|symbolic-image questions, step-by-step prompt: does reasoning fix them?|--img_types ${SYM// /_SP_} --prompt_variant cot_all"
  "p4_sym_textonly|same questions WITHOUT images: how much does the model use the picture?|--img_types ${SYM// /_SP_} --no_images"
  "p5_sym_hires|same questions, min 1024 visual tokens per image: is low resolution the cause?|--img_types ${SYM// /_SP_} --min_pixels 1048576"
  "p6_sym_describe|same questions, 'describe the image first' prompt: read transcriptions to separate perception vs reasoning|--img_types ${SYM// /_SP_} --prompt_variant describe_cot"
  "lora|LoRA feasibility on this GPU + merge + evaluate merged checkpoint (pipeline check)|"
  "p1_noise_seed1234|baseline settings, only seed changed: noise floor for every comparison|--seed 1234"
  "abl_temp0|temperature 0 (presence_penalty kept): deterministic reference|--temperature 0"
)

FG=0; LIST=0; SEL=()
for a in "$@"; do
  case "$a" in --fg) FG=1;; --list) LIST=1;; all) ;; *) SEL+=("$a");; esac
done
if [[ $LIST -eq 1 ]]; then
  for e in "${EXPERIMENTS[@]}"; do IFS='|' read -r n p _ <<<"$e"; printf "%-20s %s\n" "$n" "$p"; done; exit 0
fi
mkdir -p runs
if [[ $FG -eq 0 ]]; then
  setsid nohup bash "$0" --fg "${SEL[@]:-all}" >> runs/proposal_queue.log 2>&1 < /dev/null &
  echo "queue started in background -> tail -f runs/proposal_queue.log"; exit 0
fi

log() { echo "[$(date '+%F %T')] $*"; }
gpu_used() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU" | head -1; }
wait_gpu_free() {
  local waited=0
  while [[ $(gpu_used) -gt 1000 ]]; do
    # kill only orphaned vLLM engines of this user (parent already gone)
    for pid in $(pgrep -u "$USER" -f "VLLM::EngineCore"); do
      [[ "$(ps -o ppid= -p "$pid" | xargs)" == "1" ]] && { log "killing orphan EngineCore $pid"; kill "$pid"; }
    done
    sleep 30; waited=$((waited+30))
    [[ $waited -ge 1800 ]] && { log "GPU still busy after 30 min ($(gpu_used) MiB). Another job? stopping queue."; exit 1; }
  done
}
done_run() { python3 -c "import json,sys;sys.exit(0 if json.load(open('$1/metrics.json')).get('status')=='completed' else 1)" 2>/dev/null; }

[[ -z "${LD_LIBRARY_PATH:-}" ]] || log "WARNING: LD_LIBRARY_PATH is set ($LD_LIBRARY_PATH); bf16 GEMM failed before with it. Run: source /data/$USER/env.sh"
log "queue start: ${SEL[*]:-all}"

for e in "${EXPERIMENTS[@]}"; do
  IFS='|' read -r name purpose extra <<<"$e"
  if [[ ${#SEL[@]} -gt 0 ]] && [[ ! " ${SEL[*]} " =~ " ${name%%_*} " ]] && [[ ! " ${SEL[*]} " =~ " $name " ]]; then continue; fi
  log "=== $name : $purpose"

  if [[ "$name" == "lora" ]]; then
    if ! python -c "import peft" 2>/dev/null; then log "peft not installed -> pip install peft ; skipping lora"; continue; fi
    if [[ -f runs/lora_smoke/lora_smoke_summary.json && -f runs/lora_smoke_eval/metrics.json ]]; then log "lora already done, skip"; continue; fi
    wait_gpu_free
    python code/lora_smoke_train.py --mmmu_dev_smoke --max_steps 30 --out_dir runs/lora_smoke --save_adapter \
      > runs/lora_smoke_train.log 2>&1 || { log "lora training FAILED, see runs/lora_smoke_train.log"; continue; }
    log "lora train done: $(python3 -c "import json;s=json.load(open('runs/lora_smoke/lora_smoke_summary.json'));print(f\"peak {s['peak_mem_gb']:.1f} GB, {s['sec_per_step_mean']} s/step, ooms {s['ooms']}\")")"
    mkdir -p "$CKPT_DIR"
    python code/merge_lora.py --adapter runs/lora_smoke/adapter --out "$CKPT_DIR/lora_smoke_merged" \
      > runs/lora_smoke_merge.log 2>&1 || { log "merge FAILED, see runs/lora_smoke_merge.log"; continue; }
    wait_gpu_free
    MODEL_PATH="$CKPT_DIR/lora_smoke_merged" bash scripts/run_baseline_modelcard.sh --fg --gpu "$GPU" \
      --run_name lora_smoke_eval -- --subjects Art,Accounting --max_new_tokens 4096 >/dev/null 2>&1
    log "lora pipeline check (merged ckpt evaluated on 2 subjects): $(python3 -c "import json;print(json.load(open('runs/lora_smoke_eval/metrics.json'))['overall_percent'])" 2>/dev/null || echo FAILED)"
    continue
  fi

  if done_run "runs/$name"; then log "$name already completed, skip"; continue; fi
  if [[ -d "runs/$name" ]]; then
    mv "runs/$name" "runs/${name}_incomplete_$(date +%m%d%H%M)"; log "moved incomplete runs/$name aside"
  fi
  wait_gpu_free
  # shellcheck disable=SC2086
  read -r -a ARGS <<<"$extra"
  for i in "${!ARGS[@]}"; do ARGS[$i]="${ARGS[$i]//_SP_/ }"; done
  start=$(date +%s)
  bash scripts/run_baseline_modelcard.sh --fg --gpu "$GPU" --run_name "$name" -- "${ARGS[@]}" >/dev/null 2>&1
  st=$?
  log "$name finished exit=$st in $(( ($(date +%s)-start)/60 )) min"
done

log "building comparison table"
RUNS=$(ls -d runs/p[0-9]_* runs/abl_* runs/lora_smoke_eval 2>/dev/null | grep -v incomplete | tr '\n' ' ')
NOISE=""; [[ -f runs/p1_noise_seed1234/metrics.json ]] && NOISE="--noise runs/p1_noise_seed1234"
python code/compare_runs.py --baseline "$BASELINE" $NOISE $RUNS --out runs/proposal_table.md || true
log "queue done"
