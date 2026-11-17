# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.72 GB |
| 총 소요 시간 | 15356 s (4.27 h) 전체 / 추론 15226 s / 모델 로드 130 s |
| 실행 시각 | 2026-11-08T22:08:51+09:00 → 2026-11-09T02:24:46+09:00 |
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
| 1 | Accounting | 30 | 83.33 | 15.1m | 5760 | 32583 | 3 | 0 |
| 2 | Agriculture | 30 | 63.33 | 48s | 378 | 628 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 53.33 | 23.0m | 10670 | 32505 | 3 | 1 |
| 4 | Art | 30 | 66.67 | 511s | 1503 | 32062 | 1 | 0 |
| 5 | Art_Theory | 30 | 70.00 | 43s | 473 | 2600 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 34s | 503 | 2201 | 0 | 0 |
| 7 | Biology | 30 | 50.00 | 77s | 868 | 4840 | 0 | 0 |
| 8 | Chemistry | 30 | 40.00 | 553s | 3359 | 32598 | 1 | 0 |
| 9 | Clinical_Medicine | 30 | 56.67 | 512s | 1885 | 31880 | 1 | 0 |
| 10 | Computer_Science | 30 | 76.67 | 162s | 2286 | 8789 | 0 | 0 |
| 11 | Design | 30 | 73.33 | 30s | 439 | 1885 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 36.67 | 57s | 726 | 2861 | 0 | 0 |
| 13 | Economics | 30 | 80.00 | 121s | 1197 | 8151 | 0 | 0 |
| 14 | Electronics | 30 | 46.67 | 11.5m | 5930 | 32529 | 1 | 0 |
| 15 | Energy_and_Power | 30 | 56.67 | 33.5m | 13089 | 32570 | 8 | 2 |
| 16 | Finance | 30 | 73.33 | 183s | 2223 | 10279 | 0 | 0 |
| 17 | Geography | 30 | 56.67 | 14.6m | 4471 | 32551 | 3 | 0 |
| 18 | History | 30 | 73.33 | 57s | 900 | 3253 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 18s | 346 | 849 | 0 | 0 |
| 20 | Manage | 30 | 76.67 | 176s | 1605 | 11544 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 304s | 1667 | 19771 | 0 | 0 |
| 22 | Materials | 30 | 53.33 | 13.7m | 7776 | 32334 | 2 | 0 |
| 23 | Math | 30 | 63.33 | 10.2m | 4284 | 31969 | 1 | 0 |
| 24 | Mechanical_Engineering | 30 | 46.67 | 25.7m | 9444 | 32520 | 6 | 1 |
| 25 | Music | 30 | 20.00 | 27.9m | 8719 | 32609 | 7 | 0 |
| 26 | Pharmacy | 30 | 80.00 | 526s | 2177 | 32591 | 1 | 0 |
| 27 | Physics | 30 | 76.67 | 530s | 2218 | 32596 | 1 | 0 |
| 28 | Psychology | 30 | 73.33 | 94s | 716 | 6292 | 0 | 0 |
| 29 | Public_Health | 30 | 86.67 | 146s | 1917 | 8542 | 0 | 0 |
| 30 | Sociology | 30 | 60.00 | 509s | 1434 | 31873 | 1 | 0 |
|  | **Overall (macro avg)** | **900** | **64.33** | 253.4m |  |  | 40 | 4 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 64.33%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 64.33 |
| 차이 (Δ) | -3.07 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 860, 'length': 40}` → length(잘림) 40건 중 오답 30건
- 파싱 실패(prediction=None): 4건, 실행 오류: 0건
- completion tokens 전체: mean 3299 / median 623 / p90 8667 / p99 32565 / max 32609
- completion tokens 정답: median 505 (mean 2046) vs 오답: median 1103 (mean 5558)
- prompt tokens: mean 631 / max 5653
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 261, 'B': 210, 'C': 203, 'D': 149, 'E': 18, 'F': 1, 'I': 1, None: 4}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 66.23 |
| open | 53 | 33.96 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 62.74 |
| Easy | 295 | 76.27 |
| Hard | 181 | 48.62 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 63.23 |
| ['Tables'] | 170 | 79.41 |
| ['Plots and Charts'] | 78 | 70.51 |
| ['Photographs'] | 75 | 66.67 |
| ['Paintings'] | 46 | 65.22 |
| ['Chemical Structures'] | 30 | 30.00 |
| ['Sheet Music'] | 30 | 20.00 |
| ['Medical Images'] | 21 | 61.90 |
| ['Microscopic Images'] | 20 | 55.00 |
| ['Comics and Cartoons'] | 19 | 68.42 |
| ['Geometric Shapes'] | 17 | 76.47 |
| ['Technical Blueprints'] | 14 | 28.57 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_3 | Music | 32609 | length | False |
| validation_Music_8 | Music | 32607 | length | False |
| validation_Chemistry_7 | Chemistry | 32598 | length | True |
| validation_Physics_29 | Physics | 32596 | length | False |
| validation_Pharmacy_17 | Pharmacy | 32591 | length | False |
| validation_Accounting_9 | Accounting | 32583 | length | False |
| validation_Accounting_22 | Accounting | 32574 | length | True |
| validation_Energy_and_Power_14 | Energy_and_Power | 32570 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 32565 | length | False |
| validation_Geography_25 | Geography | 32551 | length | True |
