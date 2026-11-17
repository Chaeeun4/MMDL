# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.50 GB |
| 총 소요 시간 | 1577 s (0.44 h) 전체 / 추론 1463 s / 모델 로드 114 s |
| 실행 시각 | 2026-11-16T20:08:58+09:00 → 2026-11-16T20:35:15+09:00 |
| git | `jina` @ `6289df4e306bbe8fbcaf464c351febddc9203786` dirty=True |

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
| 1 | Accounting | 30 | 60.00 | 41s | 904 | 2272 | 0 | 0 |
| 2 | Agriculture | 30 | 66.67 | 56s | 593 | 729 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 40.00 | 58s | 1552 | 3293 | 0 | 0 |
| 4 | Art | 30 | 60.00 | 19s | 567 | 826 | 0 | 0 |
| 5 | Art_Theory | 30 | 60.00 | 24s | 631 | 912 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 80.00 | 20s | 610 | 1096 | 0 | 0 |
| 7 | Biology | 30 | 43.33 | 29s | 725 | 1323 | 0 | 0 |
| 8 | Chemistry | 30 | 30.00 | 26s | 801 | 1507 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 63.33 | 22s | 681 | 1145 | 0 | 0 |
| 10 | Computer_Science | 30 | 56.67 | 39s | 847 | 2223 | 0 | 0 |
| 11 | Design | 30 | 76.67 | 19s | 555 | 900 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 26.67 | 31s | 687 | 906 | 0 | 0 |
| 13 | Economics | 30 | 66.67 | 25s | 638 | 1505 | 0 | 0 |
| 14 | Electronics | 30 | 43.33 | 39s | 1166 | 2331 | 0 | 0 |
| 15 | Energy_and_Power | 30 | 56.67 | 39s | 1306 | 2013 | 0 | 0 |
| 16 | Finance | 30 | 53.33 | 41s | 918 | 2513 | 0 | 0 |
| 17 | Geography | 30 | 50.00 | 30s | 718 | 1717 | 0 | 0 |
| 18 | History | 30 | 66.67 | 23s | 709 | 956 | 0 | 0 |
| 19 | Literature | 30 | 86.67 | 18s | 516 | 704 | 0 | 0 |
| 20 | Manage | 30 | 50.00 | 25s | 728 | 1367 | 0 | 0 |
| 21 | Marketing | 30 | 70.00 | 27s | 754 | 1339 | 0 | 0 |
| 22 | Materials | 30 | 40.00 | 44s | 1400 | 2291 | 0 | 0 |
| 23 | Math | 30 | 60.00 | 52s | 967 | 3246 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 56.67 | 57s | 1234 | 3397 | 0 | 0 |
| 25 | Music | 30 | 50.00 | 28s | 682 | 1089 | 0 | 0 |
| 26 | Pharmacy | 30 | 60.00 | 21s | 668 | 1185 | 0 | 0 |
| 27 | Physics | 30 | 50.00 | 29s | 789 | 1774 | 0 | 0 |
| 28 | Psychology | 30 | 66.67 | 23s | 636 | 917 | 0 | 0 |
| 29 | Public_Health | 30 | 80.00 | 516s | 1847 | 32455 | 1 | 1 |
| 30 | Sociology | 30 | 66.67 | 21s | 577 | 847 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **57.89** | 24.1m |  |  | 1 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 57.89%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 57.89 |
| 차이 (Δ) | -9.51 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 899, 'length': 1}` → length(잘림) 1건 중 오답 1건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 847 / median 675 / p90 1353 / p99 2303 / max 32455
- completion tokens 정답: median 631 (mean 739) vs 오답: median 756 (mean 996)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 243, 'B': 217, 'C': 217, 'D': 147, 'E': 19, 'F': 2, 'G': 1, None: 1}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 59.74 |
| open | 53 | 28.30 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 56.13 |
| Easy | 295 | 68.14 |
| Hard | 181 | 45.30 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 56.05 |
| ['Tables'] | 170 | 63.53 |
| ['Plots and Charts'] | 78 | 56.41 |
| ['Photographs'] | 75 | 65.33 |
| ['Paintings'] | 46 | 56.52 |
| ['Chemical Structures'] | 30 | 30.00 |
| ['Sheet Music'] | 30 | 50.00 |
| ['Medical Images'] | 21 | 66.67 |
| ['Microscopic Images'] | 20 | 60.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 70.59 |
| ['Technical Blueprints'] | 14 | 35.71 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Public_Health_24 | Public_Health | 32455 | length | False |
| validation_Mechanical_Engineering_10 | Mechanical_Engineering | 3397 | stop | False |
| validation_Architecture_and_Engineering_6 | Architecture_and_Engineering | 3293 | stop | True |
| validation_Math_22 | Math | 3246 | stop | False |
| validation_Public_Health_29 | Public_Health | 2783 | stop | False |
| validation_Finance_1 | Finance | 2513 | stop | True |
| validation_Architecture_and_Engineering_7 | Architecture_and_Engineering | 2370 | stop | False |
| validation_Electronics_7 | Electronics | 2331 | stop | False |
| validation_Mechanical_Engineering_19 | Mechanical_Engineering | 2303 | stop | True |
| validation_Architecture_and_Engineering_3 | Architecture_and_Engineering | 2301 | stop | True |
