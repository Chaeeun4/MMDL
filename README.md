# MMDL Team Project — Multimodal Deep Learning

## Overview

**Goal**: Qwen3-VL-4B-Instruct를 fine-tuning하여 MMMU / MMMU-Pro 벤치마크 성능을 개선
 
| 항목 | 값 |
|---|---|
| Base model | [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) |
| Technical report | https://arxiv.org/abs/2511.21631 |
| Quick start | https://github.com/QwenLM/Qwen3-VL |
| Official MMMU | 67.4 |
| Official MMMU-Pro | 53.2 |

## Team

- **팀명**: _(기입)_
- **팀원**: _(기입)_


## Repository Structure
 
```
MMDL/
├── reports/
│   └── mmmu_baseline.md        # Baseline evaluation 리포트 (SUBMISSION_TEMPLATE.md 기반)
├── code/
├── results/
└── README.md
```
 
## Assignment #1 — Baseline Evaluation
 
**목표**: Qwen3-VL-4B-Instruct를 MMMU validation set(30개 과목, 총 900문제)으로 직접 평가
 
**제출 위치**: `reports/mmmu_baseline.md`
 
**보고 내용**:
- 과목별 + 종합(macro average) 성능
- 공식 수치(67.4)와의 비교 및 격차 분석
- 평가 코드 (MMMU 데이터 경로를 인자로 받는 스크립트)
- 실행 방법 (한 커맨드로 재현 가능해야 함)
- 실험 환경/설정 (HW 인프라, 패키지 버전 포함)
- 전체 소요 시간 및 과목별 소요 시간

