# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.55 GB |
| 총 소요 시간 | 7976 s (2.22 h) 전체 / 추론 7871 s / 모델 로드 104 s |
| 실행 시각 | 2026-11-15T14:50:38+09:00 → 2026-11-15T17:03:34+09:00 |
| git | `jina` @ `62ecc471851d277c8f4d46e0e975e868aa3b525a` dirty=True |

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
| 1 | Accounting | 30 | 70.00 | 18.0m | 6163 | 32611 | 4 | 0 |
| 2 | Agriculture | 30 | 56.67 | 26s | 8 | 24 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 43.33 | 19.1m | 8952 | 32584 | 3 | 0 |
| 4 | Art | 30 | 63.33 | 4s | 5 | 13 | 0 | 0 |
| 5 | Art_Theory | 30 | 70.00 | 5s | 5 | 14 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 19s | 54 | 1439 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 96s | 593 | 6363 | 0 | 0 |
| 8 | Chemistry | 30 | 30.00 | 127s | 798 | 8798 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 60.00 | 510s | 1113 | 32476 | 1 | 0 |
| 10 | Computer_Science | 30 | 53.33 | 149s | 790 | 10125 | 0 | 0 |
| 11 | Design | 30 | 73.33 | 3s | 6 | 19 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 40.00 | 10s | 3 | 17 | 0 | 0 |
| 13 | Economics | 30 | 70.00 | 86s | 677 | 6022 | 0 | 0 |
| 14 | Electronics | 30 | 43.33 | 557s | 2517 | 32510 | 1 | 0 |
| 15 | Energy_and_Power | 30 | 63.33 | 18.8m | 7685 | 32602 | 4 | 1 |
| 16 | Finance | 30 | 66.67 | 121s | 1565 | 6901 | 0 | 0 |
| 17 | Geography | 30 | 53.33 | 130s | 676 | 8952 | 0 | 0 |
| 18 | History | 30 | 70.00 | 9s | 28 | 385 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 14s | 33 | 891 | 0 | 0 |
| 20 | Manage | 30 | 43.33 | 107s | 550 | 7518 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 199s | 1176 | 13294 | 0 | 0 |
| 22 | Materials | 30 | 46.67 | 13.0m | 6945 | 32371 | 2 | 0 |
| 23 | Math | 30 | 63.33 | 197s | 1849 | 12113 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 40.00 | 18.8m | 6508 | 32584 | 4 | 0 |
| 25 | Music | 30 | 30.00 | 28s | 65 | 1837 | 0 | 0 |
| 26 | Pharmacy | 30 | 63.33 | 11s | 67 | 743 | 0 | 0 |
| 27 | Physics | 30 | 63.33 | 101s | 989 | 6698 | 0 | 0 |
| 28 | Psychology | 30 | 73.33 | 12s | 95 | 615 | 0 | 0 |
| 29 | Public_Health | 30 | 90.00 | 71s | 980 | 4382 | 0 | 0 |
| 30 | Sociology | 30 | 60.00 | 5s | 4 | 25 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **59.67** | 130.9m |  |  | 19 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 59.67%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 59.67 |
| 차이 (Δ) | -7.73 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 881, 'length': 19}` → length(잘림) 19건 중 오답 14건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 1697 / median 8 / p90 4720 / p99 32495 / max 32611
- completion tokens 정답: median 9 (mean 1177) vs 오답: median 6 (mean 2466)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 234, 'B': 184, 'C': 252, 'D': 151, 'E': 23, 'F': 1, 'I': 1, None: 1}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 62.46 |
| open | 53 | 15.09 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 57.78 |
| Easy | 295 | 70.85 |
| Hard | 181 | 45.86 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 58.74 |
| ['Tables'] | 170 | 73.53 |
| ['Plots and Charts'] | 78 | 57.69 |
| ['Photographs'] | 75 | 60.00 |
| ['Paintings'] | 46 | 58.70 |
| ['Chemical Structures'] | 30 | 30.00 |
| ['Sheet Music'] | 30 | 30.00 |
| ['Medical Images'] | 21 | 57.14 |
| ['Microscopic Images'] | 20 | 65.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 64.71 |
| ['Technical Blueprints'] | 14 | 35.71 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Accounting_22 | Accounting | 32611 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | False |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32584 | length | True |
| validation_Mechanical_Engineering_11 | Mechanical_Engineering | 32584 | length | False |
| validation_Accounting_17 | Accounting | 32578 | length | True |
| validation_Accounting_2 | Accounting | 32559 | length | True |
| validation_Electronics_17 | Electronics | 32510 | length | False |
| validation_Architecture_and_Engineering_8 | Architecture_and_Engineering | 32509 | length | False |
| validation_Energy_and_Power_20 | Energy_and_Power | 32495 | length | False |
| validation_Mechanical_Engineering_14 | Mechanical_Engineering | 32489 | length | True |
