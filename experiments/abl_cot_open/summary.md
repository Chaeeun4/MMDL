# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 20.92 GB |
| 총 소요 시간 | 2385 s (0.66 h) 전체 / 추론 2279 s / 모델 로드 105 s |
| 실행 시각 | 2026-10-03T15:37:47+09:00 → 2026-10-03T16:17:32+09:00 |
| git | `jina` @ `53eafc2f511cfad6734d32f59c6284cfc3be11cf` dirty=True |

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
| 3 | Architecture_and_Engineering | 1 | 0.00 | 216s | 15172 | 15172 | 0 | 0 |
| 6 | Basic_Medical_Science | 2 | 0.00 | 32s | 1442 | 2505 | 0 | 0 |
| 7 | Biology | 1 | 0.00 | 23s | 1833 | 1833 | 0 | 0 |
| 8 | Chemistry | 7 | 28.57 | 10.5m | 10341 | 32631 | 2 | 0 |
| 10 | Computer_Science | 3 | 66.67 | 19s | 1222 | 1353 | 0 | 0 |
| 13 | Economics | 1 | 100.00 | 2s | 173 | 173 | 0 | 0 |
| 14 | Electronics | 14 | 7.14 | 582s | 6872 | 32628 | 1 | 0 |
| 16 | Finance | 8 | 37.50 | 57s | 1731 | 4070 | 0 | 0 |
| 17 | Geography | 3 | 66.67 | 43s | 1526 | 3296 | 0 | 0 |
| 20 | Manage | 6 | 83.33 | 117s | 2057 | 8694 | 0 | 0 |
| 21 | Marketing | 1 | 100.00 | 4s | 337 | 337 | 0 | 0 |
| 23 | Math | 1 | 0.00 | 8s | 672 | 672 | 0 | 0 |
| 26 | Pharmacy | 3 | 100.00 | 508s | 11215 | 32488 | 1 | 0 |
| 27 | Physics | 1 | 0.00 | 9s | 713 | 713 | 0 | 0 |
| 28 | Psychology | 1 | 100.00 | 5s | 393 | 393 | 0 | 0 |
|  | **Overall (macro avg)** | **53** | **45.99** | 37.6m |  |  | 4 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 39.62%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 45.99 |
| 차이 (Δ) | -21.41 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 49, 'length': 4}` → length(잘림) 4건 중 오답 3건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 4884 / median 1286 / p90 15172 / p99 32631 / max 32631
- completion tokens 정답: median 684 (mean 2262) vs 오답: median 2882 (mean 6605)
- prompt tokens: mean 326 / max 1203
- visual tokens/sample: mean 228 / median 144 / max 1102
- 객관식 예측 분포: `{}` vs 정답 분포: `{}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| open | 53 | 39.62 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 27 | 51.85 |
| Hard | 16 | 12.50 |
| Easy | 10 | 50.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 20 | 35.00 |
| ['Tables'] | 16 | 62.50 |
| ['Chemical Structures'] | 5 | 20.00 |
| ['Plots and Charts'] | 4 | 50.00 |
| ['Diagrams', 'Technical Blueprints'] | 2 | 0.00 |
| ['Geometric Shapes'] | 2 | 0.00 |
| ['Trees and Graphs'] | 1 | 0.00 |
| ['Other'] | 1 | 100.00 |
| ['Sketches and Drafts'] | 1 | 0.00 |
| ['Diagrams', 'Mathematical Notations'] | 1 | 0.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Chemistry_20 | Chemistry | 32631 | length | False |
| validation_Electronics_29 | Electronics | 32628 | length | False |
| validation_Pharmacy_19 | Pharmacy | 32488 | length | True |
| validation_Chemistry_23 | Chemistry | 32253 | length | False |
| validation_Electronics_6 | Electronics | 16658 | stop | False |
| validation_Architecture_and_Engineering_14 | Architecture_and_Engineering | 15172 | stop | False |
| validation_Electronics_21 | Electronics | 11687 | stop | False |
| validation_Electronics_30 | Electronics | 9006 | stop | False |
| validation_Manage_3 | Manage | 8694 | stop | False |
| validation_Electronics_16 | Electronics | 6077 | stop | False |
