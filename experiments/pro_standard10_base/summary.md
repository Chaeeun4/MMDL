# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.64 GB |
| 총 소요 시간 | 38828 s (10.79 h) 전체 / 추론 38755 s / 모델 로드 73 s |
| 실행 시각 | 2026-11-22T08:08:59+09:00 → 2026-11-22T18:56:07+09:00 |
| git | `jina` @ `156d954325ddf08a959b3d62af6fa91bd7bcd46a` dirty=True |

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
| 1 | Accounting | 58 | 67.24 | 31.7m | 5897 | 32535 | 8 | 0 |
| 2 | Agriculture | 60 | 23.33 | 49s | 14 | 408 | 0 | 0 |
| 3 | Architecture_and_Engineering | 60 | 50.00 | 91.2m | 16591 | 32513 | 23 | 0 |
| 4 | Art | 53 | 56.60 | 9s | 7 | 15 | 0 | 0 |
| 5 | Art_Theory | 55 | 65.45 | 9s | 6 | 15 | 0 | 0 |
| 6 | Basic_Medical_Science | 52 | 38.46 | 83s | 171 | 5982 | 0 | 0 |
| 7 | Biology | 59 | 35.59 | 11.0m | 1679 | 32323 | 2 | 0 |
| 8 | Chemistry | 60 | 35.00 | 14.8m | 2715 | 32540 | 3 | 0 |
| 9 | Clinical_Medicine | 59 | 30.51 | 49s | 70 | 3253 | 0 | 0 |
| 10 | Computer_Science | 60 | 51.67 | 21.3m | 3915 | 32590 | 5 | 0 |
| 11 | Design | 60 | 56.67 | 5s | 7 | 33 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 60 | 28.33 | 18s | 6 | 18 | 0 | 0 |
| 13 | Economics | 59 | 61.02 | 540s | 1284 | 32569 | 1 | 0 |
| 14 | Electronics | 60 | 51.67 | 79.2m | 14746 | 32512 | 19 | 0 |
| 15 | Energy_and_Power | 58 | 39.66 | 93.3m | 16785 | 32558 | 25 | 0 |
| 16 | Finance | 60 | 75.00 | 20.6m | 4724 | 32488 | 4 | 0 |
| 17 | Geography | 52 | 53.85 | 29.1m | 2241 | 32540 | 3 | 1 |
| 18 | History | 56 | 48.21 | 15s | 15 | 390 | 0 | 0 |
| 19 | Literature | 52 | 65.38 | 7s | 5 | 15 | 0 | 0 |
| 20 | Manage | 50 | 48.00 | 566s | 2069 | 32224 | 1 | 0 |
| 21 | Marketing | 59 | 69.49 | 24.7m | 4412 | 32262 | 6 | 0 |
| 22 | Materials | 60 | 41.67 | 68.7m | 12711 | 32556 | 17 | 0 |
| 23 | Math | 60 | 60.00 | 15.8m | 3853 | 32516 | 3 | 0 |
| 24 | Mechanical_Engineering | 59 | 37.29 | 69.9m | 12208 | 32492 | 18 | 0 |
| 25 | Music | 60 | 31.67 | 10.6m | 1133 | 32534 | 2 | 0 |
| 26 | Pharmacy | 57 | 59.65 | 10.7m | 1526 | 32501 | 2 | 0 |
| 27 | Physics | 60 | 53.33 | 11.3m | 2558 | 32473 | 2 | 0 |
| 28 | Psychology | 60 | 41.67 | 51s | 134 | 3173 | 0 | 0 |
| 29 | Public_Health | 58 | 74.14 | 17.9m | 3538 | 32419 | 4 | 0 |
| 30 | Sociology | 54 | 42.59 | 13s | 10 | 284 | 0 | 0 |
|  | **Overall (macro avg)** | **1730** | **49.77** | 645.4m |  |  | 148 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 49.65%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 49.77 |
| 차이 (Δ) | -17.63 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 1581, 'length': 148, 'error': 1}` → length(잘림) 148건 중 오답 123건
- 파싱 실패(prediction=None): 1건, 실행 오류: 1건
- completion tokens 전체: mean 3923 / median 12 / p90 12839 / p99 32524 / max 32590
- completion tokens 정답: median 83 (mean 2097) vs 오답: median 8 (mean 5726)
- prompt tokens: mean 672 / max 6472
- visual tokens/sample: mean 506 / median 216 / max 6400
- 객관식 예측 분포: `{'A': 267, 'B': 202, 'C': 290, 'D': 211, 'E': 142, 'F': 134, 'G': 107, 'H': 127, 'I': 148, 'J': 100, 'L': 1, None: 1}` vs 정답 분포: `{'A': 204, 'B': 210, 'C': 199, 'D': 201, 'E': 182, 'F': 161, 'G': 144, 'H': 166, 'I': 133, 'J': 130}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 1730 | 49.65 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 801 | 50.06 |
| Easy | 528 | 58.14 |
| Hard | 401 | 37.66 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 411 | 45.99 |
| ['Tables'] | 355 | 67.89 |
| ['Photographs'] | 150 | 40.67 |
| ['Plots and Charts'] | 141 | 53.90 |
| ['Paintings'] | 100 | 58.00 |
| ['Chemical Structures'] | 63 | 34.92 |
| ['Sheet Music'] | 61 | 32.79 |
| ['Comics and Cartoons'] | 37 | 56.76 |
| ['Microscopic Images'] | 34 | 35.29 |
| ['Geometric Shapes'] | 32 | 53.12 |
| ['Medical Images'] | 30 | 26.67 |
| ['Pathological Images'] | 29 | 24.14 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| test_Computer_Science_141 | Computer_Science | 32590 | length | False |
| test_Computer_Science_351 | Computer_Science | 32574 | length | True |
| test_Economics_210 | Economics | 32569 | length | False |
| test_Energy_and_Power_220 | Energy_and_Power | 32558 | length | False |
| validation_Materials_6 | Materials | 32556 | length | False |
| validation_Energy_and_Power_14 | Energy_and_Power | 32553 | length | False |
| test_Energy_and_Power_423 | Energy_and_Power | 32551 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 32548 | length | False |
| test_Chemistry_21 | Chemistry | 32540 | length | False |
| test_Geography_398 | Geography | 32540 | length | True |
