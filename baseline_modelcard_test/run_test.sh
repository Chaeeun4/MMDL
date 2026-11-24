#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export HF_HOME="${HF_HOME:-/shared_dir/huggingface_cache}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
model_revision=ebb281ec70b05090aa6165b016eac8ec08e71b17
model_path="${MODEL_PATH:-/shared_dir/.cache/huggingface/hub/models--Qwen--Qwen3-VL-4B-Instruct/snapshots/$model_revision}"
run_dir="${RUN_DIR:-runs/baseline_modelcard_v1_mmmu_test_98e6}"
answer_path="${ANSWER_PATH:-answer_dict_test.json}"
test -s "$model_path/config.json" || { echo "Missing model config at $model_path" >&2; exit 1; }

if [[ ! -s "$answer_path" ]]; then
    temp_answer=$(mktemp)
    trap 'rm -f "$temp_answer"' EXIT
    curl -fsSL --retry 3 https://raw.githubusercontent.com/MMMU-Benchmark/MMMU/main/mmmu/answer_dict_test.json -o "$temp_answer"
    mv "$temp_answer" "$answer_path"
    trap - EXIT
fi

data_root="${DATA_ROOT:-$(python -c 'from datasets.config import HF_DATASETS_CACHE; print(HF_DATASETS_CACHE)')}"
exec python -u code/run_mmmu.py \
    --model_path "$model_path" --data_root "$data_root" --answer_path "$answer_path" \
    --run_dir "$run_dir" --batch_mode subject --logprobs 5 \
    --seed 3407 --temperature 0.7 --top_p 0.8 --top_k 20 \
    --repetition_penalty 1.0 --presence_penalty 1.5 --max_new_tokens 32768 \
    --min_pixels auto --max_pixels auto --max_model_len 32768 --gpu_memory_utilization 0.90 \
    "$@"
