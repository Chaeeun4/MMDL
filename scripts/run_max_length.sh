#!/bin/bash

set -e

# 네트워크 볼륨으로 모델 캐시 경로 고정
export HF_HOME="/workspace/huggingface_cache"

# vLLM 멀티프로세싱 CUDA 충돌 방지
export VLLM_WORKER_MULTIPROC_METHOD=spawn

MODEL="Qwen/Qwen3-VL-4B-Instruct"
DATA_ROOT="/workspace/huggingface_cache"

N=10

# 결과 저장 디렉토리 생성
mkdir -p results

echo "============================================================"
echo "MMMU max_new_tokens experiment"
echo "Samples: $N"
echo "Token settings: 32768, 16384, 8192"
echo "============================================================"


echo ""
echo "===== max_new_tokens=32768 ====="

python code/run_mmmu.py \
    --model_path "$MODEL" \
    --data_root "$DATA_ROOT" \
    --max_samples "$N" \
    --max_new_tokens 32768 \
    --output_file results/32768_predictions.jsonl \
    --metrics_file results/32768_metrics.json


echo ""
echo "===== max_new_tokens=16384 ====="

python code/run_mmmu.py \
    --model_path "$MODEL" \
    --data_root "$DATA_ROOT" \
    --max_samples "$N" \
    --max_new_tokens 16384 \
    --output_file results/16384_predictions.jsonl \
    --metrics_file results/16384_metrics.json


echo ""
echo "===== max_new_tokens=8192 ====="

python code/run_mmmu.py \
    --model_path "$MODEL" \
    --data_root "$DATA_ROOT" \
    --max_samples "$N" \
    --max_new_tokens 8192 \
    --output_file results/8192_predictions.jsonl \
    --metrics_file results/8192_metrics.json


echo ""
echo "============================================================"
echo "===== ALL TOKEN EXPERIMENTS DONE ====="
echo "============================================================"