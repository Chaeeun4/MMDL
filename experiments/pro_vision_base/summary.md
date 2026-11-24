# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 23.49 GB |
| 총 소요 시간 | 19746 s (5.48 h) 전체 / 추론 19635 s / 모델 로드 111 s |
| 실행 시각 | 2026-11-23T04:17:17+09:00 → 2026-11-23T09:46:23+09:00 |
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
| 1 | Accounting | 58 | 51.72 | 14.6m | 2102 | 31625 | 3 | 0 |
| 2 | Agriculture | 60 | 20.00 | 37s | 8 | 23 | 0 | 0 |
| 3 | Architecture_and_Engineering | 60 | 31.67 | 39.6m | 6304 | 32010 | 9 | 1 |
| 4 | Art | 53 | 45.28 | 43s | 6 | 13 | 0 | 0 |
| 5 | Art_Theory | 55 | 52.73 | 42s | 5 | 12 | 0 | 0 |
| 6 | Basic_Medical_Science | 52 | 34.62 | 38s | 6 | 12 | 0 | 0 |
| 7 | Biology | 59 | 32.20 | 52s | 5 | 17 | 0 | 0 |
| 8 | Chemistry | 60 | 26.67 | 575s | 981 | 31865 | 1 | 0 |
| 9 | Clinical_Medicine | 59 | 32.20 | 49s | 5 | 11 | 0 | 0 |
| 10 | Computer_Science | 60 | 45.00 | 165s | 229 | 7595 | 0 | 1 |
| 11 | Design | 60 | 41.67 | 50s | 5 | 19 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 60 | 25.00 | 34s | 6 | 17 | 0 | 0 |
| 13 | Economics | 59 | 47.46 | 520s | 663 | 28611 | 1 | 0 |
| 14 | Electronics | 60 | 35.00 | 27.5m | 3919 | 32217 | 6 | 0 |
| 15 | Energy_and_Power | 58 | 27.59 | 61.3m | 9841 | 32265 | 16 | 0 |
| 16 | Finance | 60 | 38.33 | 15.8m | 2596 | 31457 | 3 | 0 |
| 17 | Geography | 52 | 36.54 | 537s | 752 | 29040 | 1 | 0 |
| 18 | History | 56 | 37.50 | 57s | 7 | 41 | 0 | 0 |
| 19 | Literature | 52 | 67.31 | 49s | 5 | 13 | 0 | 0 |
| 20 | Manage | 50 | 40.00 | 121s | 331 | 3948 | 0 | 0 |
| 21 | Marketing | 59 | 55.93 | 15.1m | 2229 | 32331 | 3 | 0 |
| 22 | Materials | 60 | 30.00 | 40.2m | 6575 | 31719 | 9 | 1 |
| 23 | Math | 60 | 45.00 | 269s | 768 | 13481 | 0 | 1 |
| 24 | Mechanical_Engineering | 59 | 25.42 | 23.1m | 3590 | 32173 | 5 | 0 |
| 25 | Music | 60 | 20.00 | 46s | 4 | 13 | 0 | 1 |
| 26 | Pharmacy | 57 | 49.12 | 568s | 773 | 32194 | 1 | 1 |
| 27 | Physics | 60 | 28.33 | 11.0m | 1108 | 31523 | 2 | 0 |
| 28 | Psychology | 60 | 25.00 | 61s | 5 | 24 | 0 | 0 |
| 29 | Public_Health | 58 | 39.66 | 21.4m | 2976 | 31665 | 5 | 1 |
| 30 | Sociology | 54 | 40.74 | 42s | 5 | 20 | 0 | 0 |
|  | **Overall (macro avg)** | **1730** | **37.59** | 325.6m |  |  | 65 | 7 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 37.34%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 37.59 |
| 차이 (Δ) | -29.81 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 1665, 'length': 65}` → length(잘림) 65건 중 오답 57건
- 파싱 실패(prediction=None): 7건, 실행 오류: 0건
- completion tokens 전체: mean 1561 / median 6 / p90 1698 / p99 31545 / max 32331
- completion tokens 정답: median 6 (mean 883) vs 오답: median 6 (mean 1965)
- prompt tokens: mean 2952 / max 8756
- visual tokens/sample: mean 2929 / median 2270 / max 8733
- 객관식 예측 분포: `{'A': 309, 'B': 304, 'C': 271, 'D': 196, 'E': 100, 'F': 158, 'G': 95, 'H': 115, 'I': 87, 'J': 87, 'K': 1, None: 7}` vs 정답 분포: `{'A': 204, 'B': 210, 'C': 199, 'D': 201, 'E': 182, 'F': 161, 'G': 144, 'H': 166, 'I': 133, 'J': 130}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 1730 | 37.34 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| (blank) | 1730 | 37.34 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| (blank) | 1730 | 37.34 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| test_Marketing_62 | Marketing | 32331 | length | False |
| validation_Energy_and_Power_15 | Energy_and_Power | 32265 | length | False |
| test_Electronics_178 | Electronics | 32217 | length | False |
| validation_Pharmacy_1 | Pharmacy | 32194 | length | True |
| test_Mechanical_Engineering_62 | Mechanical_Engineering | 32173 | length | True |
| validation_Mechanical_Engineering_23 | Mechanical_Engineering | 32095 | length | False |
| validation_Energy_and_Power_14 | Energy_and_Power | 32070 | length | False |
| test_Architecture_and_Engineering_206 | Architecture_and_Engineering | 32010 | length | False |
| validation_Electronics_10 | Electronics | 31975 | length | False |
| test_Electronics_67 | Electronics | 31953 | length | False |
