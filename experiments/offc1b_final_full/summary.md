# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.50 GB |
| 총 소요 시간 | 16725 s (4.65 h) 전체 / 추론 16589 s / 모델 로드 136 s |
| 실행 시각 | 2026-11-16T12:28:07+09:00 → 2026-11-16T17:06:52+09:00 |
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
| 1 | Accounting | 30 | 76.67 | 12.2m | 4971 | 32361 | 2 | 1 |
| 2 | Agriculture | 30 | 56.67 | 45s | 390 | 795 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 70.00 | 33.1m | 13338 | 32584 | 6 | 0 |
| 4 | Art | 30 | 63.33 | 510s | 1371 | 32099 | 1 | 0 |
| 5 | Art_Theory | 30 | 76.67 | 37s | 470 | 2050 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 76.67 | 29s | 464 | 1922 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 82s | 921 | 5089 | 0 | 0 |
| 8 | Chemistry | 30 | 36.67 | 563s | 3548 | 32269 | 1 | 0 |
| 9 | Clinical_Medicine | 30 | 66.67 | 63s | 813 | 4115 | 0 | 0 |
| 10 | Computer_Science | 30 | 63.33 | 552s | 2943 | 32372 | 1 | 0 |
| 11 | Design | 30 | 80.00 | 26s | 380 | 1619 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 33.33 | 48s | 674 | 2075 | 0 | 0 |
| 13 | Economics | 30 | 83.33 | 522s | 2036 | 32488 | 1 | 0 |
| 14 | Electronics | 30 | 43.33 | 516s | 5912 | 21071 | 0 | 0 |
| 15 | Energy_and_Power | 30 | 63.33 | 31.2m | 12088 | 32607 | 7 | 1 |
| 16 | Finance | 30 | 73.33 | 548s | 3026 | 32368 | 1 | 0 |
| 17 | Geography | 30 | 56.67 | 139s | 1605 | 8575 | 0 | 0 |
| 18 | History | 30 | 76.67 | 54s | 720 | 3357 | 0 | 0 |
| 19 | Literature | 30 | 76.67 | 518s | 1518 | 32599 | 1 | 1 |
| 20 | Manage | 30 | 66.67 | 10.8m | 3226 | 32384 | 2 | 0 |
| 21 | Marketing | 30 | 83.33 | 243s | 1793 | 14640 | 0 | 0 |
| 22 | Materials | 30 | 56.67 | 21.3m | 9910 | 32591 | 4 | 0 |
| 23 | Math | 30 | 60.00 | 580s | 3825 | 32006 | 1 | 0 |
| 24 | Mechanical_Engineering | 30 | 50.00 | 27.6m | 10313 | 32552 | 6 | 0 |
| 25 | Music | 30 | 43.33 | 31.9m | 9567 | 32644 | 8 | 0 |
| 26 | Pharmacy | 30 | 86.67 | 523s | 2057 | 32504 | 1 | 0 |
| 27 | Physics | 30 | 76.67 | 523s | 2289 | 32444 | 1 | 0 |
| 28 | Psychology | 30 | 76.67 | 91s | 782 | 6024 | 0 | 0 |
| 29 | Public_Health | 30 | 90.00 | 188s | 1797 | 11858 | 0 | 0 |
| 30 | Sociology | 30 | 66.67 | 27s | 410 | 1487 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **66.11** | 275.1m |  |  | 44 | 3 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 66.11%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 66.11 |
| 차이 (Δ) | -1.29 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 856, 'length': 44}` → length(잘림) 44건 중 오답 24건
- 파싱 실패(prediction=None): 3건, 실행 오류: 0건
- completion tokens 전체: mean 3439 / median 556 / p90 9987 / p99 32552 / max 32644
- completion tokens 정답: median 475 (mean 2523) vs 오답: median 1118 (mean 5224)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 267, 'B': 216, 'C': 188, 'D': 150, 'E': 21, 'F': 2, None: 3}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 67.53 |
| open | 53 | 43.40 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 65.09 |
| Easy | 295 | 74.24 |
| Hard | 181 | 55.25 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 65.47 |
| ['Tables'] | 170 | 79.41 |
| ['Plots and Charts'] | 78 | 70.51 |
| ['Photographs'] | 75 | 66.67 |
| ['Paintings'] | 46 | 65.22 |
| ['Chemical Structures'] | 30 | 33.33 |
| ['Sheet Music'] | 30 | 43.33 |
| ['Medical Images'] | 21 | 66.67 |
| ['Microscopic Images'] | 20 | 65.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 64.71 |
| ['Technical Blueprints'] | 14 | 50.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_8 | Music | 32644 | length | True |
| validation_Music_28 | Music | 32641 | length | False |
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | True |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | False |
| validation_Literature_10 | Literature | 32599 | length | False |
| validation_Materials_6 | Materials | 32591 | length | True |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32584 | length | True |
| validation_Energy_and_Power_22 | Energy_and_Power | 32561 | length | False |
| validation_Mechanical_Engineering_23 | Mechanical_Engineering | 32552 | length | False |
| validation_Energy_and_Power_17 | Energy_and_Power | 32546 | length | True |
