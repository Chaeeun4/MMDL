#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

usage() {
    cat <<'EOF'
Usage: scripts/run_mmmu_controlled.sh {pilot|seeds|context|full} [--dry-run]
  pilot    Base and PrIMuS step 500, 60 questions, seed 3407, 32K context
  seeds    Same pair, seeds 1234, 42, 2026, 7777 (run pilot for seed 3407)
  context  Base only, 60 questions, seed 3407, 16K context (compare with pilot)
  full     Base and PrIMuS step 500, 900 questions, seed 3407, 32K context

Environment: PRIMUS_MODEL_PATH points to the merged step-500 checkpoint.
Optional: BASE_MODEL_PATH, MMMU_CACHE, PYTHON_BIN, MMMU_CONTROLLED_OUT.
EOF
}

if [[ ${1:-} == --help || ${1:-} == -h ]]; then
    usage
    exit 0
fi
mode="${1:-}"
dry_run=false
if [[ ${2:-} == --dry-run ]]; then dry_run=true; fi
if (( $# > 2 )) || [[ -n ${2:-} && $dry_run == false ]]; then
    usage >&2
    exit 2
fi

python_bin="${PYTHON_BIN:-python3}"
base_model="${BASE_MODEL_PATH:-Qwen/Qwen3-VL-4B-Instruct}"
primus_model="${PRIMUS_MODEL_PATH:-/shared_dir/merged_models/qwen3vl_4b_primus_only}"
cache="${MMMU_CACHE:-${HF_HOME:-/workspace/huggingface_cache}}"
output="${MMMU_CONTROLLED_OUT:-runs/controlled_legacy_cot}"
export VLLM_WORKER_MULTIPROC_METHOD="${VLLM_WORKER_MULTIPROC_METHOD:-spawn}"

models=(base primus_only)
seeds=(3407)
subset=60q
context=32768
subjects=(--subjects Music,Chemistry)
case "$mode" in
    pilot) ;;
    seeds) seeds=(1234 42 2026 7777) ;;
    context) models=(base); context=16384 ;;
    full) subset=900q; subjects=() ;;
    *) usage >&2; exit 2 ;;
esac

if [[ $dry_run == false && $mode != context && ! -f "$primus_model/config.json" ]]; then
    printf 'Merged PrIMuS step-500 checkpoint missing. Set PRIMUS_MODEL_PATH (currently %s).\n' "$primus_model" >&2
    exit 1
fi

for seed in "${seeds[@]}"; do
    for model in "${models[@]}"; do
        model_path="$base_model"
        if [[ $model == primus_only ]]; then model_path="$primus_model"; fi
        result="$output/$subset/context-$context/seed-$seed/$model"
        cmd=("$python_bin" -u code/run_mmmu.py
            --model_path "$model_path" --data_root "$cache" --run_dir "$result"
            "${subjects[@]}" --batch_mode subject --seed "$seed"
            --prompt_variant legacy_cot --max_model_len "$context"
            --temperature 0.7 --top_p 0.8 --top_k 20
            --repetition_penalty 1.0 --presence_penalty 1.5 --max_new_tokens 32768
            --min_pixels 65536 --max_pixels 16777216
            --gpu_memory_utilization 0.80 --logprobs 0)
        if [[ $dry_run == true ]]; then
            printf '%q ' "${cmd[@]}"
            printf '\n'
        else
            if [[ -e "$result" ]]; then
                printf 'Output already exists: %s. Select a fresh MMMU_CONTROLLED_OUT.\n' "$result" >&2
                exit 1
            fi
            mkdir -p "$result"
            "${cmd[@]}" 2>&1 | tee "$result/run.log"
        fi
    done
done
