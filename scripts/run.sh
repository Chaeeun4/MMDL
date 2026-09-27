#!/bin/bash

# 네트워크 볼륨으로 모델 캐시 경로 고정 (파드 재생성 시 데이터 증발 방지)
export HF_HOME="/workspace/huggingface_cache"

echo "🏃 모델 평가 파이프라인을 실행합니다..."
# 전달받은 모든 인자("$@")를 파이썬 스크립트로 전달
python code/run_mmmu.py "$@"