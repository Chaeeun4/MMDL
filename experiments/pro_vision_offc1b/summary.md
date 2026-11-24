# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 23.12 GB |
| 총 소요 시간 | 36273 s (10.08 h) 전체 / 추론 36167 s / 모델 로드 105 s |
| 실행 시각 | 2026-11-23T09:46:50+09:00 → 2026-11-23T19:51:23+09:00 |
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
| 1 | Accounting | 58 | 72.41 | 20.3m | 3805 | 32147 | 4 | 0 |
| 2 | Agriculture | 60 | 20.00 | 157s | 622 | 7081 | 0 | 0 |
| 3 | Architecture_and_Engineering | 60 | 35.00 | 85.6m | 14806 | 32445 | 19 | 0 |
| 4 | Art | 53 | 52.83 | 106s | 593 | 2374 | 0 | 0 |
| 5 | Art_Theory | 55 | 56.36 | 94s | 524 | 1386 | 0 | 0 |
| 6 | Basic_Medical_Science | 52 | 48.08 | 267s | 978 | 12463 | 0 | 0 |
| 7 | Biology | 59 | 38.98 | 12.5m | 2160 | 32043 | 2 | 0 |
| 8 | Chemistry | 60 | 41.67 | 26.3m | 4515 | 31865 | 6 | 0 |
| 9 | Clinical_Medicine | 59 | 30.51 | 131s | 683 | 1912 | 0 | 0 |
| 10 | Computer_Science | 60 | 56.67 | 13.7m | 3011 | 31545 | 2 | 0 |
| 11 | Design | 60 | 53.33 | 149s | 633 | 3948 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 60 | 26.67 | 101s | 693 | 1748 | 0 | 0 |
| 13 | Economics | 59 | 74.58 | 576s | 1440 | 28611 | 1 | 0 |
| 14 | Electronics | 60 | 55.00 | 70.0m | 12363 | 32331 | 15 | 0 |
| 15 | Energy_and_Power | 58 | 46.55 | 62.3m | 11762 | 32265 | 12 | 0 |
| 16 | Finance | 60 | 85.00 | 16.9m | 3569 | 31457 | 2 | 1 |
| 17 | Geography | 52 | 34.62 | 12.4m | 2083 | 32361 | 2 | 0 |
| 18 | History | 56 | 53.57 | 149s | 781 | 2497 | 0 | 0 |
| 19 | Literature | 52 | 67.31 | 576s | 1104 | 31625 | 1 | 1 |
| 20 | Manage | 50 | 60.00 | 11.8m | 2543 | 28000 | 2 | 0 |
| 21 | Marketing | 59 | 64.41 | 16.9m | 3313 | 31940 | 3 | 0 |
| 22 | Materials | 60 | 40.00 | 55.9m | 10051 | 32241 | 12 | 0 |
| 23 | Math | 60 | 56.67 | 18.2m | 3867 | 32265 | 3 | 1 |
| 24 | Mechanical_Engineering | 59 | 30.51 | 52.3m | 9964 | 32437 | 10 | 0 |
| 25 | Music | 60 | 20.00 | 46.1m | 7334 | 32422 | 12 | 2 |
| 26 | Pharmacy | 57 | 59.65 | 10.2m | 2021 | 29385 | 1 | 0 |
| 27 | Physics | 60 | 53.33 | 313s | 1645 | 9424 | 0 | 0 |
| 28 | Psychology | 60 | 46.67 | 163s | 801 | 3531 | 0 | 0 |
| 29 | Public_Health | 58 | 70.69 | 21.9m | 3864 | 31825 | 5 | 0 |
| 30 | Sociology | 54 | 55.56 | 82s | 493 | 974 | 0 | 0 |
|  | **Overall (macro avg)** | **1730** | **50.22** | 601.1m |  |  | 114 | 5 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 50.06%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 50.22 |
| 차이 (Δ) | -17.18 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 1616, 'length': 114}` → length(잘림) 114건 중 오답 98건
- 파싱 실패(prediction=None): 5건, 실행 오류: 0건
- completion tokens 전체: mean 3808 / median 694 / p90 10958 / p99 32125 / max 32445
- completion tokens 정답: median 610 (mean 2192) vs 오답: median 834 (mean 5427)
- prompt tokens: mean 2952 / max 8756
- visual tokens/sample: mean 2929 / median 2270 / max 8733
- 객관식 예측 분포: `{'A': 250, 'B': 238, 'C': 208, 'D': 200, 'E': 141, 'F': 143, 'G': 136, 'H': 148, 'I': 139, 'J': 122, None: 5}` vs 정답 분포: `{'A': 204, 'B': 210, 'C': 199, 'D': 201, 'E': 182, 'F': 161, 'G': 144, 'H': 166, 'I': 133, 'J': 130}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 1730 | 50.06 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| (blank) | 1730 | 50.06 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| (blank) | 1730 | 50.06 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| test_Architecture_and_Engineering_214 | Architecture_and_Engineering | 32445 | length | False |
| test_Mechanical_Engineering_203 | Mechanical_Engineering | 32437 | length | False |
| validation_Music_1 | Music | 32422 | length | True |
| test_Geography_428 | Geography | 32361 | length | False |
| test_Music_116 | Music | 32361 | length | False |
| validation_Music_7 | Music | 32345 | length | False |
| test_Electronics_123 | Electronics | 32331 | length | False |
| test_Electronics_213 | Electronics | 32285 | length | True |
| validation_Energy_and_Power_1 | Energy_and_Power | 32265 | length | False |
| test_Math_165 | Math | 32265 | length | False |
