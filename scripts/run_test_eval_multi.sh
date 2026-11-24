#!/usr/bin/env bash
# MMMU test (10,500 questions, pinned revision, evaluation only) on several GPUs of one machine.
# Same recipe as scripts/run_test_eval.sh (official prompt, official sampling, seed 3407); the 30 subjects are
# split into 6 groups and every group is evaluated for all models on ONE GPU (base first, then the tuned
# model), so the two models are always compared on the same hardware.
#
# Needs no /data/$USER layout: activate the Python environment first, everything else lives under $WORK.
#   source ~/venv-mmdl/bin/activate
#   setsid nohup bash scripts/run_test_eval_multi.sh > ~/mmdl_work/test_eval.log 2>&1 < /dev/null &
#   bash scripts/run_test_eval_multi.sh --status        # progress per group
#   DRY_RUN=1 bash scripts/run_test_eval_multi.sh       # print the plan only
# Env: GPUS="0 1 2 3 4 5"  MODELS="base offc1b"  WORK=~/mmdl_work  HF_HOME=$WORK/hf_cache
# Rerun the same command to resume: finished subjects are skipped.
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GPUS="${GPUS:-0 1 2 3 4 5}"
MODELS="${MODELS:-base offc1b}"
WORK="${WORK:-$HOME/mmdl_work}"
export HF_HOME="${HF_HOME:-$WORK/hf_cache}"
CKPT="$WORK/ckpt"; OUT="$WORK/test_eval"
mkdir -p "$WORK" "$HF_HOME" "$CKPT" "$OUT" runs
GROUPS_=(
  "Literature,Diagnostics_and_Laboratory_Medicine,Design,Marketing,Art"
  "Manage,Sociology,Electronics,Economics,History"
  "Agriculture,Psychology,Clinical_Medicine,Basic_Medical_Science,Music"
  "Biology,Finance,Computer_Science,Accounting,Physics"
  "Mechanical_Engineering,Art_Theory,Pharmacy,Energy_and_Power,Materials"
  "Math,Public_Health,Architecture_and_Engineering,Geography,Chemistry"
)
read -ra GPU_LIST <<< "$GPUS"
log() { echo "[$(date '+%F %T')] $*"; }
model_path() { [[ "$1" == base ]] && echo "Qwen/Qwen3-VL-4B-Instruct" || echo "$CKPT/${1}_ft_merged"; }
done_all() {  # done_all <run> <subjects,csv>: every subject has a per-subject checkpoint
  local s; IFS=',' read -ra subs <<< "$2"
  for s in "${subs[@]}"; do [[ -f "runs/$1/per_subject/$s.jsonl" ]] || return 1; done
}

if [[ "${1:-}" == "--status" ]]; then
  for gi in "${!GROUPS_[@]}"; do for m in $MODELS; do
    run="test_${m}_g$((gi+1))"; n=$(ls "runs/$run/per_subject" 2>/dev/null | wc -l)
    last=$(tr '\r' '\n' < "runs/$run/run.log" 2>/dev/null | grep running_acc | tail -1 | sed 's/.*| //' || true)
    echo "group $((gi+1)) $m: $n/5 subjects  $last"
  done; done
  exit 0
fi

log "GPUs: ${GPU_LIST[*]} | models: $MODELS | work dir: $WORK"
for gi in "${!GROUPS_[@]}"; do
  log "plan: group $((gi+1)) -> GPU ${GPU_LIST[$((gi % ${#GPU_LIST[@]}))]} [${GROUPS_[$gi]}]"
done
[[ "${DRY_RUN:-0}" == 1 ]] && exit 0

# ---- 1. one-time downloads in a single process (parallel workers must not race on the HF cache) ----------
if [[ ! -f "$WORK/PREFETCH_DONE" ]]; then
  log "prefetch base model and the MMMU test split"
  ( cd code && python - "$HF_HOME" <<'PY'
import sys
from huggingface_hub import snapshot_download
from datasets import load_dataset
from dataset import DATASET_NAME, DATASET_REVISION, SUBJECTS
snapshot_download("Qwen/Qwen3-VL-4B-Instruct", revision="ebb281ec70b05090aa6165b016eac8ec08e71b17")
n = 0
for s in SUBJECTS:
    n += len(load_dataset(DATASET_NAME, s, split="test", revision=DATASET_REVISION, cache_dir=sys.argv[1]))
print("MMMU test questions:", n)
assert n == 10500, n
PY
  )
  touch "$WORK/PREFETCH_DONE"
fi

# ---- 2. tuned models: adapter from artifacts/ (split parts) -> merged checkpoint -------------------------
for m in $MODELS; do
  [[ "$m" == base ]] && continue
  merged="$(model_path "$m")"
  [[ -f "$merged/MERGED_FROM.txt" ]] && continue
  src="artifacts/checkpoints/${m}_ft"; ad="$CKPT/${m}_ft_adapter"
  [[ -f "$src/adapter_config.json" ]] || { log "missing $src"; exit 1; }
  log "restore adapter $m and merge"
  rm -rf "$ad" "$merged"; mkdir -p "$ad"
  cp "$src/adapter_config.json" "$ad/"
  cat "$src"/adapter_model.safetensors.part* > "$ad/adapter_model.safetensors"
  ( cd "$ad" && sha256sum -c "$OLDPWD/$src/SHA256SUMS" )
  CUDA_VISIBLE_DEVICES="${GPU_LIST[0]}" python code/merge_lora.py --adapter "$ad" --out "$merged"
done

# ---- 3. one worker per GPU; a worker runs its groups one after the other, base then tuned ----------------
worker() {  # worker <gpu> <group index>...
  local gpu="$1"; shift
  local gi m run used i resume
  for gi in "$@"; do
    for m in $MODELS; do
      run="test_${m}_g$((gi+1))"
      done_all "$run" "${GROUPS_[$gi]}" && { log "gpu $gpu: $run already done"; continue; }
      for i in $(seq 1 288); do  # wait while someone else holds this GPU
        used=$(nvidia-smi -i "$gpu" --query-gpu=memory.used --format=csv,noheader,nounits)
        (( used < 1000 )) && break; (( i % 12 == 1 )) && log "gpu $gpu busy (${used} MiB) - waiting"; sleep 300
      done
      resume=(); [[ -d "runs/$run/per_subject" ]] && resume=(--resume)
      log "gpu $gpu: eval $run"
      MODEL_PATH="$(model_path "$m")" DATA_ROOT="$HF_HOME" PYTHON=python \
        bash scripts/run_baseline_modelcard.sh --fg --gpu "$gpu" --run_name "$run" "${resume[@]}" \
        -- --benchmark mmmu_test --prompt_variant official --subjects "${GROUPS_[$gi]}" \
        > "$OUT/$run.launcher.log" 2>&1 || log "gpu $gpu: $run exited non-zero (see runs/$run/run.log)"
      sleep 20
    done
  done
  log "gpu $gpu: worker done"
}
pids=()
for wi in "${!GPU_LIST[@]}"; do
  mine=(); for gi in "${!GROUPS_[@]}"; do (( gi % ${#GPU_LIST[@]} == wi )) && mine+=("$gi"); done
  [[ ${#mine[@]} -gt 0 ]] || continue
  worker "${GPU_LIST[$wi]}" "${mine[@]}" & pids+=($!)
  sleep 30  # stagger engine start-up
done
for p in "${pids[@]}"; do wait "$p" || true; done

# ---- 4. collect the per-subject files into runs/test_<model> and score all 30 subjects -------------------
ok=1
for m in $MODELS; do
  mkdir -p "runs/test_$m/per_subject"
  for gi in "${!GROUPS_[@]}"; do
    run="test_${m}_g$((gi+1))"
    done_all "$run" "${GROUPS_[$gi]}" || { log "NOT finished: $run"; ok=0; continue; }
    cp "runs/$run"/per_subject/*.jsonl "runs/test_$m/per_subject/"
  done
done
if [[ $ok == 1 ]]; then
  for m in $MODELS; do
    [[ -f "runs/test_$m/FULL_DONE" ]] && continue
    log "final scoring test_$m (nothing left to generate)"
    MODEL_PATH="$(model_path "$m")" DATA_ROOT="$HF_HOME" PYTHON=python \
      bash scripts/run_baseline_modelcard.sh --fg --gpu "${GPU_LIST[0]}" --run_name "test_$m" --resume \
      -- --benchmark mmmu_test --prompt_variant official > "$OUT/test_$m.launcher.log" 2>&1 || log "test_$m exited non-zero"
    grep -q '"num_results": 10500' "runs/test_$m/metrics.json" && touch "runs/test_$m/FULL_DONE"
  done
else
  log "some groups are unfinished: rerun the same command to resume"
fi
first="${MODELS%% *}"; rest=()
for m in $MODELS; do [[ "$m" != "$first" && -d "runs/test_$m/per_subject" ]] && rest+=("runs/test_$m"); done
[[ ${#rest[@]} -gt 0 ]] && python code/compare_runs.py --baseline "runs/test_$first" "${rest[@]}" --out "$OUT/compare.md" || true
log "test eval done -> $OUT/compare.md"
