# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 23.56 GB |
| 총 소요 시간 | 23602 s (6.56 h) 전체 / 추론 23498 s / 모델 로드 103 s |
| 실행 시각 | 2026-10-05T19:25:13+09:00 → 2026-10-06T01:58:35+09:00 |
| git | `jina` @ `47b95cee9d58bff966f4cb1f81b50f84d0c7a26c` dirty=True |

## 생성 설정

| 파라미터 | 값 |
|---|---|
| `greedy` | False |
| `seed` | 3407 |
| `temperature` | 0.0 |
| `top_p` | 0.8 |
| `top_k` | 20 |
| `repetition_penalty` | 1.0 |
| `presence_penalty` | 1.5 |
| `max_new_tokens` | 32768 |
| `logprobs` | 5 |
| `min_pixels` | 65536 |
| `max_pixels` | 16777216 |
| 공식 recipe 일치 | False |

## 결과

| No. | Subject | Data Num | Acc | 소요 시간 | 평균 토큰 | 최대 토큰 | length stop | parse 실패 |
|---|---|---|---|---|---|---|---|---|
| 1 | Accounting | 30 | 63.33 | 30.1m | 9472 | 32620 | 8 | 1 |
| 2 | Agriculture | 30 | 53.33 | 26s | 9 | 24 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 30.00 | 50.9m | 16874 | 32584 | 14 | 2 |
| 4 | Art | 30 | 60.00 | 5s | 6 | 13 | 0 | 0 |
| 5 | Art_Theory | 30 | 76.67 | 5s | 5 | 14 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 2s | 7 | 28 | 0 | 0 |
| 7 | Biology | 30 | 50.00 | 10.2m | 2319 | 31996 | 2 | 0 |
| 8 | Chemistry | 30 | 33.33 | 10.4m | 2957 | 32418 | 2 | 0 |
| 9 | Clinical_Medicine | 30 | 66.67 | 3s | 6 | 19 | 0 | 0 |
| 10 | Computer_Science | 30 | 56.67 | 513s | 1579 | 32501 | 1 | 0 |
| 11 | Design | 30 | 76.67 | 3s | 6 | 19 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 36.67 | 10s | 5 | 17 | 0 | 0 |
| 13 | Economics | 30 | 66.67 | 10.4m | 2690 | 32565 | 2 | 1 |
| 14 | Electronics | 30 | 43.33 | 20.1m | 6100 | 32602 | 5 | 0 |
| 15 | Energy_and_Power | 30 | 60.00 | 53.5m | 17252 | 32607 | 15 | 3 |
| 16 | Finance | 30 | 63.33 | 20.0m | 5791 | 32503 | 5 | 0 |
| 17 | Geography | 30 | 56.67 | 14.0m | 3524 | 32599 | 3 | 0 |
| 18 | History | 30 | 70.00 | 4s | 10 | 29 | 0 | 0 |
| 19 | Literature | 30 | 76.67 | 504s | 1087 | 32482 | 1 | 1 |
| 20 | Manage | 30 | 40.00 | 506s | 1403 | 32392 | 1 | 0 |
| 21 | Marketing | 30 | 83.33 | 10.2m | 2508 | 31916 | 2 | 1 |
| 22 | Materials | 30 | 56.67 | 47.2m | 15571 | 32591 | 13 | 1 |
| 23 | Math | 30 | 63.33 | 14.5m | 4900 | 32575 | 3 | 0 |
| 24 | Mechanical_Engineering | 30 | 33.33 | 40.0m | 12336 | 32584 | 11 | 3 |
| 25 | Music | 30 | 33.33 | 500s | 1152 | 31878 | 1 | 0 |
| 26 | Pharmacy | 30 | 63.33 | 28s | 136 | 2162 | 0 | 0 |
| 27 | Physics | 30 | 56.67 | 10.4m | 2884 | 32589 | 2 | 0 |
| 28 | Psychology | 30 | 73.33 | 9s | 37 | 422 | 0 | 0 |
| 29 | Public_Health | 30 | 83.33 | 14.1m | 3952 | 32555 | 3 | 1 |
| 30 | Sociology | 30 | 60.00 | 5s | 5 | 25 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **58.56** | 391.3m |  |  | 94 | 14 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 58.56%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 58.56 |
| 차이 (Δ) | -8.84 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 806, 'length': 94}` → length(잘림) 94건 중 오답 72건
- 파싱 실패(prediction=None): 14건, 실행 오류: 0건
- completion tokens 전체: mean 3819 / median 8 / p90 31878 / p99 32589 / max 32620
- completion tokens 정답: median 9 (mean 1829) vs 오답: median 8 (mean 6631)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 230, 'B': 206, 'C': 229, 'D': 145, 'E': 21, 'F': 2, None: 14}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 61.39 |
| open | 53 | 13.21 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 57.31 |
| Easy | 295 | 69.83 |
| Hard | 181 | 43.09 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 56.50 |
| ['Tables'] | 170 | 68.24 |
| ['Plots and Charts'] | 78 | 61.54 |
| ['Photographs'] | 75 | 62.67 |
| ['Paintings'] | 46 | 60.87 |
| ['Chemical Structures'] | 30 | 33.33 |
| ['Sheet Music'] | 30 | 33.33 |
| ['Medical Images'] | 21 | 66.67 |
| ['Microscopic Images'] | 20 | 55.00 |
| ['Comics and Cartoons'] | 19 | 68.42 |
| ['Geometric Shapes'] | 17 | 76.47 |
| ['Technical Blueprints'] | 14 | 28.57 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Accounting_9 | Accounting | 32620 | length | True |
| validation_Accounting_22 | Accounting | 32611 | length | False |
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | False |
| validation_Electronics_7 | Electronics | 32602 | length | True |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | False |
| validation_Geography_5 | Geography | 32599 | length | False |
| validation_Materials_6 | Materials | 32591 | length | False |
| validation_Energy_and_Power_21 | Energy_and_Power | 32589 | length | True |
| validation_Physics_9 | Physics | 32589 | length | False |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32584 | length | False |
