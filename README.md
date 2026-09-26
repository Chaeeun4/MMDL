# MMDL Team Project — Multimodal Deep Learning

## Overview

**Goal**: Qwen3-VL-4B-Instruct를 fine-tuning하여 MMMU / MMMU-Pro 벤치마크 성능을 개선

  
| 항목 | 값 |
|---|---|
| Base model | [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) |
| Official MMMU | 67.4 |
| Official MMMU-Pro | 53.2 |

### Target Benchmarks
 
**MMMU** (Massive Multi-discipline Multimodal Understanding)
- Multi-domain, college-level multimodal reasoning benchmark
- Multiple-choice + short-answer questions, 30 categories
- Metric: accuracy
- Split: Dev 150 (미사용) / Validation 900 (baseline 평가에 사용) / Test 10,500
  
**MMMU-Pro**
- MMMU 기반의 더 어려운 벤치마크 — 텍스트만으로 풀리는 문제 제외, 10지선다 추가, vision-only 세팅 포함
- Test split만 존재
- 계획: MMMU validation으로 tuning → MMMU/MMMU-Pro test로 최종 평가


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

