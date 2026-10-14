# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 20.91 GB |
| 총 소요 시간 | 1152 s (0.32 h) 전체 / 추론 1050 s / 모델 로드 102 s |
| 실행 시각 | 2026-10-05T11:51:34+09:00 → 2026-10-05T12:10:46+09:00 |
| git | `jina` @ `47b95cee9d58bff966f4cb1f81b50f84d0c7a26c` dirty=True |

## 생성 설정

| 파라미터 | 값 |
|---|---|
| `greedy` | False |
| `seed` | 3407 |
| `temperature` | 0.7 |
| `top_p` | 0.8 |
| `top_k` | 20 |
| `repetition_penalty` | 1.0 |
| `presence_penalty` | 1.5 |
| `max_new_tokens` | 32768 |
| `logprobs` | 5 |
| `min_pixels` | 65536 |
| `max_pixels` | 16777216 |
| 공식 recipe 일치 | True |

## 결과

| No. | Subject | Data Num | Acc | 소요 시간 | 평균 토큰 | 최대 토큰 | length stop | parse 실패 |
|---|---|---|---|---|---|---|---|---|
| 3 | Architecture_and_Engineering | 3 | 0.00 | 2s | 15 | 27 | 0 | 0 |
| 5 | Art_Theory | 4 | 25.00 | 0s | 6 | 6 | 0 | 0 |
| 6 | Basic_Medical_Science | 2 | 0.00 | 7s | 272 | 539 | 0 | 0 |
| 7 | Biology | 2 | 50.00 | 0s | 6 | 9 | 0 | 0 |
| 8 | Chemistry | 18 | 11.11 | 4s | 61 | 293 | 0 | 0 |
| 11 | Design | 1 | 100.00 | 0s | 4 | 4 | 0 | 0 |
| 14 | Electronics | 1 | 0.00 | 0s | 3 | 3 | 0 | 0 |
| 15 | Energy_and_Power | 3 | 66.67 | 509s | 10886 | 32633 | 1 | 1 |
| 17 | Geography | 5 | 60.00 | 0s | 11 | 17 | 0 | 0 |
| 18 | History | 1 | 100.00 | 0s | 7 | 7 | 0 | 0 |
| 20 | Manage | 1 | 0.00 | 0s | 5 | 5 | 0 | 0 |
| 22 | Materials | 5 | 40.00 | 522s | 8620 | 32632 | 1 | 0 |
| 23 | Math | 1 | 0.00 | 0s | 21 | 21 | 0 | 0 |
| 24 | Mechanical_Engineering | 5 | 0.00 | 0s | 5 | 18 | 0 | 0 |
| 25 | Music | 30 | 23.33 | 0s | 5 | 13 | 0 | 0 |
| 26 | Pharmacy | 11 | 27.27 | 3s | 31 | 239 | 0 | 0 |
| 28 | Psychology | 1 | 0.00 | 0s | 4 | 4 | 0 | 0 |
| 30 | Sociology | 1 | 0.00 | 0s | 2 | 2 | 0 | 0 |
|  | **Overall (macro avg)** | **95** | **27.97** | 17.5m |  |  | 2 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 24.21%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 27.97 |
| 차이 (Δ) | -39.43 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 93, 'length': 2}` → length(잘림) 2건 중 오답 1건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 822 / median 6 / p90 185 / p99 32633 / max 32633
- completion tokens 정답: median 6 (mean 1487) vs 오답: median 6 (mean 609)
- prompt tokens: mean 76 / max 206
- 객관식 예측 분포: `{'A': 13, 'B': 24, 'C': 34, 'D': 15, None: 1}` vs 정답 분포: `{'A': 22, 'B': 29, 'C': 23, 'D': 13}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 87 | 26.44 |
| open | 8 | 0.00 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 47 | 21.28 |
| Easy | 28 | 28.57 |
| Hard | 20 | 25.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Chemical Structures'] | 30 | 20.00 |
| ['Sheet Music'] | 30 | 23.33 |
| ['Technical Blueprints'] | 14 | 35.71 |
| ['Sketches and Drafts'] | 9 | 0.00 |
| ['Diagrams', 'Technical Blueprints'] | 5 | 60.00 |
| ['Sketches and Drafts', 'Paintings'] | 2 | 50.00 |
| ['Diagrams', 'Sketches and Drafts'] | 2 | 0.00 |
| ['Photographs', 'Technical Blueprints'] | 1 | 0.00 |
| ['Sketches and Drafts', 'Medical Images'] | 1 | 0.00 |
| ['Mathematical Notations', 'Chemical Structures'] | 1 | 100.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Energy_and_Power_12 | Energy_and_Power | 32633 | length | False |
| validation_Materials_17 | Materials | 32632 | length | True |
| validation_Materials_12 | Materials | 9270 | stop | False |
| validation_Materials_7 | Materials | 1183 | stop | True |
| validation_Basic_Medical_Science_6 | Basic_Medical_Science | 539 | stop | False |
| validation_Chemistry_29 | Chemistry | 293 | stop | False |
| validation_Chemistry_12 | Chemistry | 255 | stop | False |
| validation_Chemistry_26 | Chemistry | 249 | stop | False |
| validation_Pharmacy_1 | Pharmacy | 239 | stop | True |
| validation_Chemistry_16 | Chemistry | 185 | stop | False |
