# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.41 GB |
| 총 소요 시간 | 13235 s (3.68 h) 전체 / 추론 13083 s / 모델 로드 151 s |
| 실행 시각 | 2026-10-02T13:59:51+09:00 → 2026-10-02T17:40:26+09:00 |
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
| 21 | Marketing | 30 | 90.00 | 83s | 655 | 5728 | 0 | 0 |
| 29 | Public_Health | 30 | 90.00 | 138s | 1164 | 9101 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 15s | 36 | 936 | 0 | 0 |
| 11 | Design | 30 | 76.67 | 3s | 7 | 21 | 0 | 0 |
| 5 | Art_Theory | 30 | 73.33 | 5s | 6 | 14 | 0 | 0 |
| 28 | Psychology | 30 | 73.33 | 8s | 31 | 300 | 0 | 0 |
| 1 | Accounting | 30 | 70.00 | 21.3m | 6947 | 32611 | 5 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 2s | 7 | 28 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 70.00 | 3s | 7 | 19 | 0 | 0 |
| 13 | Economics | 30 | 70.00 | 121s | 872 | 8328 | 0 | 0 |
| 18 | History | 30 | 70.00 | 4s | 12 | 29 | 0 | 0 |
| 26 | Pharmacy | 30 | 70.00 | 63s | 252 | 4729 | 0 | 0 |
| 4 | Art | 30 | 66.67 | 4s | 6 | 13 | 0 | 0 |
| 27 | Physics | 30 | 66.67 | 50s | 665 | 3269 | 0 | 0 |
| 15 | Energy_and_Power | 30 | 63.33 | 29.9m | 11248 | 32602 | 7 | 2 |
| 23 | Math | 30 | 63.33 | 252s | 2599 | 13860 | 0 | 0 |
| 16 | Finance | 30 | 60.00 | 10.9m | 3475 | 32427 | 2 | 0 |
| 30 | Sociology | 30 | 60.00 | 5s | 5 | 25 | 0 | 0 |
| 2 | Agriculture | 30 | 56.67 | 26s | 9 | 24 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 520s | 1575 | 32320 | 1 | 0 |
| 10 | Computer_Science | 30 | 53.33 | 534s | 1743 | 32637 | 1 | 0 |
| 17 | Geography | 30 | 53.33 | 524s | 1665 | 32571 | 1 | 0 |
| 3 | Architecture_and_Engineering | 30 | 50.00 | 26.3m | 10215 | 32584 | 5 | 0 |
| 14 | Electronics | 30 | 50.00 | 599s | 3277 | 32510 | 1 | 0 |
| 22 | Materials | 30 | 46.67 | 30.5m | 11160 | 32591 | 7 | 0 |
| 20 | Manage | 30 | 43.33 | 520s | 1553 | 32392 | 1 | 0 |
| 24 | Mechanical_Engineering | 30 | 43.33 | 31.1m | 10146 | 32584 | 8 | 1 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 36.67 | 10s | 5 | 17 | 0 | 0 |
| 25 | Music | 30 | 33.33 | 38s | 94 | 2677 | 0 | 0 |
| 8 | Chemistry | 30 | 30.00 | 535s | 2100 | 32635 | 1 | 0 |
|  | **Overall (macro avg)** | **900** | **61.11** | 217.7m |  |  | 40 | 3 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 61.11%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 61.11 |
| 차이 (Δ) | -6.29 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 860, 'length': 40}` → length(잘림) 40건 중 오답 31건
- 파싱 실패(prediction=None): 3건, 실행 오류: 0건
- completion tokens 전체: mean 2384 / median 8 / p90 5788 / p99 32571 / max 32637
- completion tokens 정답: median 10 (mean 1400) vs 오답: median 8 (mean 3932)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 236, 'B': 207, 'C': 235, 'D': 143, 'E': 21, 'F': 2, None: 3}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 63.87 |
| open | 53 | 16.98 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 61.32 |
| Easy | 295 | 70.17 |
| Hard | 181 | 45.86 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 60.54 |
| ['Tables'] | 170 | 73.53 |
| ['Plots and Charts'] | 78 | 60.26 |
| ['Photographs'] | 75 | 64.00 |
| ['Paintings'] | 46 | 63.04 |
| ['Chemical Structures'] | 30 | 26.67 |
| ['Sheet Music'] | 30 | 33.33 |
| ['Medical Images'] | 21 | 66.67 |
| ['Microscopic Images'] | 20 | 55.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 76.47 |
| ['Technical Blueprints'] | 14 | 28.57 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Computer_Science_8 | Computer_Science | 32637 | length | False |
| validation_Chemistry_7 | Chemistry | 32635 | length | False |
| validation_Accounting_22 | Accounting | 32611 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | False |
| validation_Materials_6 | Materials | 32591 | length | False |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32584 | length | False |
| validation_Mechanical_Engineering_11 | Mechanical_Engineering | 32584 | length | False |
| validation_Materials_4 | Materials | 32578 | length | False |
| validation_Geography_1 | Geography | 32571 | length | True |
| validation_Energy_and_Power_9 | Energy_and_Power | 32570 | length | True |
