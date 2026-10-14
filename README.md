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

- **팀명**: team4
- **팀원**: 박채은, 류다연, 이진아, 정성원

## Qwen3-VL-4B 실험 결과 요약 (이진아, branch `jina`)

공식 recipe baseline 61.1% (공식 67.4). 서술형에 단계별 풀이 프롬프트를 주면 17.0 → 39.6% (p=0.0075),
기호·도식 이미지 95문항은 "이미지 먼저 설명 후 풀이"로 32.6 → 45.3% (p≈0.05). seed 노이즈는 문항의 6.6%.
전체 표·해석·재현 방법: **[docs/qwen3vl_experiments.md](docs/qwen3vl_experiments.md)**, 원자료: `experiments/`, `evidence/`.

## Repository Structure
 
```
MMDL/
├── reports/
│   ├── mmmu_baseline.md            # Baseline evaluation 리포트 (SUBMISSION_TEMPLATE.md 기반, 4096 토큰·축소 해상도)
│   └── mmmu_baseline_modelcard.md  # 모델 카드/공식 recipe 그대로 돌린 baseline 리포트 (branch jina)
├── code/
│   ├── run_mmmu.py                 # 평가 파이프라인 (한 커맨드, 과목별 체크포인트/재개, 진단 로그)
│   ├── summarize_run.py            # run 디렉토리 → 템플릿 표 + 진단 요약 (summary.md / summary.json)
│   ├── prompt.py / parser.py / evaluator.py / dataset.py
│   └── analyze_*.py                # 오답/길이/반복 분석 스크립트
├── scripts/
│   ├── check_gpu.sh                # GPU/디스크/패키지 사전 점검
│   ├── run_baseline_modelcard.sh   # 공식 recipe baseline 을 백그라운드로 실행 (nohup, 로그/모니터링 포함)
│   ├── status_run.sh               # 진행 상황/ETA/GPU 확인
│   └── gpu_monitor.sh              # GPU 시계열 CSV
├── docs/baseline_modelcard_runbook.md   # 서버에서 실행하는 절차
├── runs/<run_name>/                # 실행 산출물 (predictions, metrics, manifest, 로그, GPU 시계열)
├── results/, log/                  # 이전 실험 결과/로그
└── README.md
```

### Quick start (model-card baseline, branch `jina`)

```bash
bash scripts/check_gpu.sh                                     # 1. 빈 GPU 확인
bash scripts/run_baseline_modelcard.sh --smoke --gpu 0        # 2. 2과목 빠른 점검 (~10분)
bash scripts/run_baseline_modelcard.sh --gpu 0 --run_name baseline_modelcard_v1   # 3. 본 실행 (백그라운드)
bash scripts/status_run.sh runs/baseline_modelcard_v1         # 4. 진행 확인
python code/summarize_run.py runs/baseline_modelcard_v1 --compare results/opt_predictions_orig.jsonl   # 5. 요약/비교
```
자세한 절차: [docs/baseline_modelcard_runbook.md](docs/baseline_modelcard_runbook.md)
 
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

