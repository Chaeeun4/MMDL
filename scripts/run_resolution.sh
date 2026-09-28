#!/bin/bash

set -e

# 네트워크 볼륨으로 모델 캐시 경로 고정
export HF_HOME="/workspace/huggingface_cache"

# vLLM 멀티프로세싱 CUDA 충돌 방지
export VLLM_WORKER_MULTIPROC_METHOD=spawn

MODEL="Qwen/Qwen3-VL-4B-Instruct"
DATA_ROOT="/workspace/huggingface_cache"

N=90

echo "============================================================"
echo "MMMU resolution experiment"
echo "Samples: $N"
echo "Resolution settings:"
echo "  1280-5120"
echo "  512-2048"
echo "  256-1280"
echo "============================================================"


echo ""
echo "===== min_pixels=1280, max_pixels=5120 ====="

python code/run_mmmu.py \
    --model_path "$MODEL" \
    --data_root "$DATA_ROOT" \
    --max_samples "$N" \
    --min_pixels $((1280 * 32 * 32)) \
    --max_pixels $((5120 * 32 * 32)) \
    --output_file results/1280-5120_predictions.jsonl \
    --metrics_file results/1280-5120_metrics.json


echo ""
echo "===== min_pixels=512, max_pixels=2048 ====="

python code/run_mmmu.py \
    --model_path "$MODEL" \
    --data_root "$DATA_ROOT" \
    --max_samples "$N" \
    --min_pixels $((512 * 32 * 32)) \
    --max_pixels $((2048 * 32 * 32)) \
    --output_file results/512-2048_predictions.jsonl \
    --metrics_file results/512-2048_metrics.json


echo ""
echo "===== min_pixels=256, max_pixels=1280 ====="

python code/run_mmmu.py \
    --model_path "$MODEL" \
    --data_root "$DATA_ROOT" \
    --max_samples "$N" \
    --min_pixels $((256 * 32 * 32)) \
    --max_pixels $((1280 * 32 * 32)) \
    --output_file results/256-1280_predictions.jsonl \
    --metrics_file results/256-1280_metrics.json


echo ""
echo "============================================================"
echo "===== ALL RESOLUTION EXPERIMENTS DONE ====="
echo "============================================================"