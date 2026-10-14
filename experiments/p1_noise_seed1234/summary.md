# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.55 GB |
| 총 소요 시간 | 15942 s (4.43 h) 전체 / 추론 15841 s / 모델 로드 101 s |
| 실행 시각 | 2026-10-05T14:59:20+09:00 → 2026-10-05T19:25:03+09:00 |
| git | `jina` @ `47b95cee9d58bff966f4cb1f81b50f84d0c7a26c` dirty=True |

## 생성 설정

| 파라미터 | 값 |
|---|---|
| `greedy` | False |
| `seed` | 1234 |
| `temperature` | 0.7 |
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
| 1 | Accounting | 30 | 70.00 | 20.8m | 6915 | 32618 | 5 | 0 |
| 2 | Agriculture | 30 | 56.67 | 26s | 9 | 24 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 36.67 | 42.3m | 15098 | 32584 | 10 | 3 |
| 4 | Art | 30 | 66.67 | 5s | 7 | 17 | 0 | 0 |
| 5 | Art_Theory | 30 | 70.00 | 5s | 6 | 14 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 2s | 8 | 28 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 60s | 484 | 3823 | 0 | 0 |
| 8 | Chemistry | 30 | 26.67 | 541s | 2206 | 32635 | 1 | 0 |
| 9 | Clinical_Medicine | 30 | 70.00 | 3s | 7 | 19 | 0 | 0 |
| 10 | Computer_Science | 30 | 60.00 | 123s | 955 | 7776 | 0 | 0 |
| 11 | Design | 30 | 76.67 | 3s | 7 | 21 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 36.67 | 10s | 6 | 20 | 0 | 0 |
| 13 | Economics | 30 | 70.00 | 133s | 866 | 9258 | 0 | 0 |
| 14 | Electronics | 30 | 50.00 | 10.2m | 3615 | 32546 | 1 | 0 |
| 15 | Energy_and_Power | 30 | 63.33 | 39.9m | 13622 | 32607 | 10 | 2 |
| 16 | Finance | 30 | 66.67 | 11.1m | 3877 | 32427 | 2 | 0 |
| 17 | Geography | 30 | 56.67 | 148s | 926 | 9990 | 0 | 0 |
| 18 | History | 30 | 70.00 | 4s | 13 | 29 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 19s | 48 | 1295 | 0 | 0 |
| 20 | Manage | 30 | 40.00 | 518s | 1501 | 32392 | 1 | 0 |
| 21 | Marketing | 30 | 86.67 | 110s | 873 | 7382 | 0 | 0 |
| 22 | Materials | 30 | 46.67 | 42.3m | 14464 | 32633 | 11 | 0 |
| 23 | Math | 30 | 63.33 | 557s | 2908 | 32006 | 1 | 0 |
| 24 | Mechanical_Engineering | 30 | 40.00 | 36.8m | 11312 | 32584 | 9 | 1 |
| 25 | Music | 30 | 26.67 | 509s | 1188 | 31878 | 1 | 0 |
| 26 | Pharmacy | 30 | 66.67 | 46s | 292 | 3301 | 0 | 0 |
| 27 | Physics | 30 | 70.00 | 109s | 1201 | 6967 | 0 | 0 |
| 28 | Psychology | 30 | 73.33 | 9s | 40 | 387 | 0 | 0 |
| 29 | Public_Health | 30 | 83.33 | 11.2m | 3670 | 32555 | 2 | 2 |
| 30 | Sociology | 30 | 56.67 | 5s | 5 | 25 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **60.11** | 263.7m |  |  | 54 | 8 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 60.11%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 60.11 |
| 차이 (Δ) | -7.29 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 846, 'length': 54}` → length(잘림) 54건 중 오답 43건
- 파싱 실패(prediction=None): 8건, 실행 오류: 0건
- completion tokens 전체: mean 2871 / median 9 / p90 7655 / p99 32578 / max 32635
- completion tokens 정답: median 10 (mean 1605) vs 오답: median 8 (mean 4778)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 243, 'B': 185, 'C': 243, 'D': 143, 'E': 23, 'F': 1, 'I': 1, None: 8}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 62.93 |
| open | 53 | 15.09 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 58.73 |
| Easy | 295 | 70.85 |
| Hard | 181 | 45.86 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 61.43 |
| ['Tables'] | 170 | 70.59 |
| ['Plots and Charts'] | 78 | 60.26 |
| ['Photographs'] | 75 | 62.67 |
| ['Paintings'] | 46 | 60.87 |
| ['Chemical Structures'] | 30 | 26.67 |
| ['Sheet Music'] | 30 | 26.67 |
| ['Medical Images'] | 21 | 61.90 |
| ['Microscopic Images'] | 20 | 60.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 70.59 |
| ['Technical Blueprints'] | 14 | 35.71 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Chemistry_7 | Chemistry | 32635 | length | True |
| validation_Materials_1 | Materials | 32633 | length | False |
| validation_Accounting_25 | Accounting | 32618 | length | False |
| validation_Accounting_22 | Accounting | 32611 | length | False |
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | False |
| validation_Materials_6 | Materials | 32591 | length | False |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32584 | length | False |
| validation_Mechanical_Engineering_11 | Mechanical_Engineering | 32584 | length | False |
| validation_Materials_4 | Materials | 32578 | length | False |
| validation_Energy_and_Power_9 | Energy_and_Power | 32570 | length | True |
