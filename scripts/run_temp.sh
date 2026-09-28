#!/usr/bin/env bash
set -euo pipefail

# 환경 변수 설정 (기본값 지정)
MODEL="${MODEL:-Qwen/Qwen3-VL-4B-Instruct}"
DATA_ROOT="${DATA_ROOT:-/root/.cache/huggingface/hub/datasets--MMMU--MMMU}"
# N="${N:--1}" # 전체 샘플(-1) 또는 테스트 샘플 수

echo "=========================================================="
echo " Starting MMMU Evaluation (Optimized)"
echo " Model: ${MODEL}"
echo " Pixels: min=256*32*32, max=1280*32*32"
echo " Max New Tokens: 4096 (무한루프 방지)"
echo "=========================================================="

python3 code/run_mmmu.py \
 --model_path "$MODEL" \
 --data_root "$DATA_ROOT" \
 --min_pixels $((256 * 32 * 32)) \
 --max_pixels $((1280 * 32 * 32)) \
 --max_new_tokens 4096 \
 --temperature 0.01 \
 --output_file results/opt_predictions_tmp.jsonl \
 --metrics_file results/opt_metrics_tmp.json

echo "tmp Evaluation Finished!"

python3 code/run_mmmu.py \
 --model_path "$MODEL" \
 --data_root "$DATA_ROOT" \
 --min_pixels $((256 * 32 * 32)) \
 --max_pixels $((1280 * 32 * 32)) \
 --max_new_tokens 4096 \
 --repetition_penalty 1.05 \
 --output_file results/opt_predictions_rep.jsonl \
 --metrics_file results/opt_metrics_rep.json

echo "repen Evaluation Finished"
