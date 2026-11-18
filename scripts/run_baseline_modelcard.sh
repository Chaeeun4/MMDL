#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# One-command MMMU-val baseline with the *official Qwen3-VL Instruct* recipe
# and the checkpoint's own (model-card) image-resolution defaults.
#
#   bash scripts/run_baseline_modelcard.sh                 # background (nohup)
#   bash scripts/run_baseline_modelcard.sh --fg            # foreground
#   bash scripts/run_baseline_modelcard.sh --gpu 1         # pick GPU
#   bash scripts/run_baseline_modelcard.sh --run_name X    # runs/X
#   bash scripts/run_baseline_modelcard.sh --resume --run_name X
#   bash scripts/run_baseline_modelcard.sh --smoke         # 2 subjects x 30 ... quick check
#   bash scripts/run_baseline_modelcard.sh -- --max_samples 10   # extra args -> run_mmmu.py
#
# Env overrides: MODEL_PATH, DATA_ROOT, HF_HOME, PYTHON, GPU_MONITOR_INTERVAL
#
# Everything the run produces lands in runs/<run_name>/ :
#   run.log, launcher.log, command.txt, pid, env.txt, pip_freeze.txt,
#   nvidia-smi_before.txt, nvidia-smi_after.txt, gpu_monitor.csv,
#   manifest.json, metrics.json, predictions.jsonl, per_subject/*.jsonl,
#   summary.md (+ summary.json) produced by code/summarize_run.py
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

FG=0
RESUME=0
SMOKE=0
GPU=""
RUN_NAME=""
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fg) FG=1; shift ;;
    --resume) RESUME=1; shift ;;
    --smoke) SMOKE=1; shift ;;
    --gpu) GPU="$2"; shift 2 ;;
    --run_name) RUN_NAME="$2"; shift 2 ;;
    --) shift; EXTRA+=("$@"); break ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done

MODEL_PATH="${MODEL_PATH:-Qwen/Qwen3-VL-4B-Instruct}"
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
DATA_ROOT="${DATA_ROOT:-$HF_HOME}"
PYTHON="${PYTHON:-python3}"
GPU_MONITOR_INTERVAL="${GPU_MONITOR_INTERVAL:-10}"
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export TOKENIZERS_PARALLELISM=false
[[ -n "$GPU" ]] && export CUDA_VISIBLE_DEVICES="$GPU"

if [[ -z "$RUN_NAME" ]]; then
  RUN_NAME="baseline_modelcard_$(date +%Y%m%d_%H%M%S)"
  [[ $SMOKE -eq 1 ]] && RUN_NAME="smoke_$(date +%Y%m%d_%H%M%S)"
fi
RUN_DIR="$REPO_DIR/runs/$RUN_NAME"
mkdir -p "$RUN_DIR"

# ---- background re-exec ---------------------------------------------------
if [[ $FG -eq 0 ]]; then
  ARGS=(--fg --run_name "$RUN_NAME")
  [[ $RESUME -eq 1 ]] && ARGS+=(--resume)
  [[ $SMOKE -eq 1 ]] && ARGS+=(--smoke)
  [[ -n "$GPU" ]] && ARGS+=(--gpu "$GPU")
  [[ ${#EXTRA[@]} -gt 0 ]] && ARGS+=(-- "${EXTRA[@]}")
  setsid nohup bash "$0" "${ARGS[@]}" > "$RUN_DIR/launcher.log" 2>&1 < /dev/null &
  LPID=$!
  echo "$LPID" > "$RUN_DIR/launcher.pid"
  echo "launched in background (launcher pid $LPID)"
  echo "run dir : $RUN_DIR"
  echo "follow  : tail -f $RUN_DIR/run.log"
  echo "status  : bash scripts/status_run.sh $RUN_DIR"
  echo "stop    : kill \$(cat $RUN_DIR/pid)"
  exit 0
fi

# ---- foreground pipeline --------------------------------------------------
{
  echo "run_name   : $RUN_NAME"
  echo "started    : $(date -Is)"
  echo "host       : $(hostname)"
  echo "user       : $(whoami)"
  echo "repo       : $REPO_DIR"
  echo "git        : $(git rev-parse --abbrev-ref HEAD 2>/dev/null)@$(git rev-parse HEAD 2>/dev/null)"
  echo "MODEL_PATH : $MODEL_PATH"
  echo "DATA_ROOT  : $DATA_ROOT"
  echo "HF_HOME    : $HF_HOME"
  echo "CUDA_VISIBLE_DEVICES : ${CUDA_VISIBLE_DEVICES:-<unset>}"
  echo "python     : $($PYTHON --version 2>&1) ($(command -v $PYTHON))"
} | tee "$RUN_DIR/env.txt"
env | sort > "$RUN_DIR/env_full.txt"
$PYTHON -m pip freeze > "$RUN_DIR/pip_freeze.txt" 2>/dev/null || true
nvidia-smi > "$RUN_DIR/nvidia-smi_before.txt" 2>&1 || true
git status --short > "$RUN_DIR/git_status.txt" 2>/dev/null || true
git diff > "$RUN_DIR/git_diff.patch" 2>/dev/null || true

CMD=("$PYTHON" code/run_mmmu.py
  --model_path "$MODEL_PATH"
  --data_root "$DATA_ROOT"
  --run_dir "$RUN_DIR"
  --batch_mode subject
  --logprobs 5
  # Official Instruct recipe (also the script defaults; spelled out so the
  # exact numbers are visible in command.txt):
  --seed 3407 --temperature 0.7 --top_p 0.8 --top_k 20
  --repetition_penalty 1.0 --presence_penalty 1.5
  --max_new_tokens 32768
  # model-card image resolution = checkpoint processor defaults
  --min_pixels auto --max_pixels auto
  --max_model_len 32768 --gpu_memory_utilization 0.90
)
[[ $RESUME -eq 1 ]] && CMD+=(--resume)
[[ $SMOKE -eq 1 ]] && CMD+=(--subjects Accounting,Art --max_new_tokens 4096)
[[ ${#EXTRA[@]} -gt 0 ]] && CMD+=("${EXTRA[@]}")

printf '%q ' "${CMD[@]}" > "$RUN_DIR/command.txt"; echo >> "$RUN_DIR/command.txt"
echo "command    : $(cat "$RUN_DIR/command.txt")"

# GPU time series in the background for the whole run.
bash scripts/gpu_monitor.sh "$RUN_DIR/gpu_monitor.csv" "$GPU_MONITOR_INTERVAL" &
MON_PID=$!
echo "$MON_PID" > "$RUN_DIR/gpu_monitor.pid"
cleanup() {
  kill "$MON_PID" 2>/dev/null || true
  nvidia-smi > "$RUN_DIR/nvidia-smi_after.txt" 2>&1 || true
  echo "finished   : $(date -Is)" | tee -a "$RUN_DIR/env.txt"
}
trap cleanup EXIT

START=$(date +%s)
set +e
"${CMD[@]}" > >(tee -a "$RUN_DIR/run.log") 2>&1 &
PY_PID=$!
echo "$PY_PID" > "$RUN_DIR/pid"
wait "$PY_PID"
STATUS=$?
set -e
END=$(date +%s)
echo "exit_status: $STATUS  wall_seconds: $((END-START))" | tee -a "$RUN_DIR/env.txt"

if [[ $STATUS -eq 0 ]]; then
  $PYTHON code/summarize_run.py "$RUN_DIR" --out "$RUN_DIR/summary.md" \
    --json "$RUN_DIR/summary.json" || echo "summarize_run.py failed (non-fatal)"
  echo "DONE -> $RUN_DIR/summary.md"
else
  echo "FAILED (exit $STATUS). See $RUN_DIR/run.log ; resume with:"
  echo "  bash scripts/run_baseline_modelcard.sh --resume --run_name $RUN_NAME"
fi
exit $STATUS
