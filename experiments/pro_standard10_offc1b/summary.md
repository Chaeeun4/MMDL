# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.64 GB |
| 총 소요 시간 | 33618 s (9.34 h) 전체 / 추론 33548 s / 모델 로드 69 s |
| 실행 시각 | 2026-11-22T18:56:33+09:00 → 2026-11-23T04:16:51+09:00 |
| git | `jina` @ `803eb0f159cf9517a4a11bfbd538880613629448` dirty=True |

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
| 1 | Accounting | 58 | 67.24 | 18.4m | 3962 | 32521 | 4 | 0 |
| 2 | Agriculture | 60 | 28.33 | 148s | 580 | 6136 | 0 | 0 |
| 3 | Architecture_and_Engineering | 60 | 53.33 | 79.8m | 15587 | 32506 | 17 | 0 |
| 4 | Art | 53 | 58.49 | 39s | 458 | 1783 | 0 | 0 |
| 5 | Art_Theory | 55 | 63.64 | 518s | 1108 | 31701 | 1 | 0 |
| 6 | Basic_Medical_Science | 52 | 53.85 | 164s | 872 | 10798 | 0 | 0 |
| 7 | Biology | 59 | 44.07 | 576s | 1996 | 32525 | 1 | 0 |
| 8 | Chemistry | 60 | 53.33 | 21.3m | 4495 | 32617 | 5 | 0 |
| 9 | Clinical_Medicine | 59 | 37.29 | 113s | 903 | 6918 | 0 | 0 |
| 10 | Computer_Science | 60 | 58.33 | 18.8m | 4362 | 32538 | 4 | 0 |
| 11 | Design | 60 | 66.67 | 39s | 488 | 2148 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 60 | 16.67 | 103s | 966 | 3844 | 0 | 0 |
| 13 | Economics | 59 | 74.58 | 111s | 1040 | 6254 | 0 | 0 |
| 14 | Electronics | 60 | 65.00 | 40.7m | 10686 | 32539 | 6 | 0 |
| 15 | Energy_and_Power | 58 | 37.93 | 68.7m | 13626 | 32558 | 17 | 0 |
| 16 | Finance | 60 | 83.33 | 23.2m | 5141 | 32385 | 5 | 0 |
| 17 | Geography | 52 | 40.38 | 28.1m | 2299 | 32476 | 2 | 1 |
| 18 | History | 56 | 50.00 | 63s | 704 | 2927 | 0 | 1 |
| 19 | Literature | 52 | 67.31 | 525s | 1107 | 32570 | 1 | 1 |
| 20 | Manage | 50 | 66.00 | 558s | 2371 | 32220 | 1 | 0 |
| 21 | Marketing | 59 | 74.58 | 12.4m | 3041 | 32069 | 2 | 0 |
| 22 | Materials | 60 | 41.67 | 40.7m | 9588 | 32556 | 8 | 0 |
| 23 | Math | 60 | 60.00 | 13.9m | 4498 | 32516 | 2 | 0 |
| 24 | Mechanical_Engineering | 59 | 37.29 | 47.4m | 10076 | 32492 | 10 | 0 |
| 25 | Music | 60 | 13.33 | 55.3m | 9313 | 32607 | 15 | 0 |
| 26 | Pharmacy | 57 | 68.42 | 577s | 2217 | 32312 | 1 | 0 |
| 27 | Physics | 60 | 60.00 | 598s | 2633 | 32538 | 1 | 0 |
| 28 | Psychology | 60 | 48.33 | 111s | 1020 | 5646 | 0 | 0 |
| 29 | Public_Health | 58 | 74.14 | 10.5m | 2813 | 32377 | 1 | 0 |
| 30 | Sociology | 54 | 53.70 | 521s | 1110 | 31819 | 1 | 1 |
|  | **Overall (macro avg)** | **1730** | **53.91** | 558.6m |  |  | 105 | 4 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 53.76%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 53.91 |
| 차이 (Δ) | -13.49 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 1624, 'length': 105, 'error': 1}` → length(잘림) 105건 중 오답 89건
- 파싱 실패(prediction=None): 4건, 실행 오류: 1건
- completion tokens 전체: mean 4049 / median 748 / p90 12050 / p99 32530 / max 32617
- completion tokens 정답: median 622 (mean 2336) vs 오답: median 1020 (mean 6043)
- prompt tokens: mean 672 / max 6472
- visual tokens/sample: mean 506 / median 216 / max 6400
- 객관식 예측 분포: `{'A': 270, 'B': 240, 'C': 230, 'D': 191, 'E': 153, 'F': 133, 'G': 125, 'H': 143, 'I': 120, 'J': 121, None: 4}` vs 정답 분포: `{'A': 204, 'B': 210, 'C': 199, 'D': 201, 'E': 182, 'F': 161, 'G': 144, 'H': 166, 'I': 133, 'J': 130}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 1730 | 53.76 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 801 | 52.43 |
| Easy | 528 | 64.58 |
| Hard | 401 | 42.14 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 411 | 49.64 |
| ['Tables'] | 355 | 74.08 |
| ['Photographs'] | 150 | 43.33 |
| ['Plots and Charts'] | 141 | 57.45 |
| ['Paintings'] | 100 | 62.00 |
| ['Chemical Structures'] | 63 | 47.62 |
| ['Sheet Music'] | 61 | 14.75 |
| ['Comics and Cartoons'] | 37 | 59.46 |
| ['Microscopic Images'] | 34 | 38.24 |
| ['Geometric Shapes'] | 32 | 59.38 |
| ['Medical Images'] | 30 | 40.00 |
| ['Pathological Images'] | 29 | 20.69 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| test_Chemistry_524 | Chemistry | 32617 | length | False |
| validation_Music_8 | Music | 32607 | length | False |
| validation_Music_9 | Music | 32589 | length | False |
| validation_Literature_10 | Literature | 32570 | length | False |
| validation_Chemistry_17 | Chemistry | 32562 | length | False |
| test_Energy_and_Power_220 | Energy_and_Power | 32558 | length | False |
| validation_Materials_6 | Materials | 32556 | length | False |
| test_Energy_and_Power_375 | Energy_and_Power | 32555 | length | False |
| validation_Energy_and_Power_14 | Energy_and_Power | 32553 | length | False |
| test_Energy_and_Power_276 | Energy_and_Power | 32543 | length | False |
