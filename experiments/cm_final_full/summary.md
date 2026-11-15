# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.72 GB |
| 총 소요 시간 | 17572 s (4.88 h) 전체 / 추론 17467 s / 모델 로드 105 s |
| 실행 시각 | 2026-11-13T20:40:20+09:00 → 2026-11-14T01:33:12+09:00 |
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
| 1 | Accounting | 30 | 70.00 | 15.2m | 5626 | 32583 | 3 | 0 |
| 2 | Agriculture | 30 | 50.00 | 46s | 396 | 704 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 60.00 | 41.2m | 15002 | 32547 | 9 | 0 |
| 4 | Art | 30 | 66.67 | 511s | 1462 | 32062 | 1 | 0 |
| 5 | Art_Theory | 30 | 76.67 | 40s | 476 | 2306 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 63.33 | 45s | 617 | 2977 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 526s | 2021 | 32283 | 1 | 1 |
| 8 | Chemistry | 30 | 50.00 | 544s | 2972 | 32230 | 1 | 0 |
| 9 | Clinical_Medicine | 30 | 63.33 | 40s | 615 | 2567 | 0 | 0 |
| 10 | Computer_Science | 30 | 66.67 | 221s | 2511 | 12317 | 0 | 0 |
| 11 | Design | 30 | 76.67 | 27s | 460 | 1623 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 26.67 | 44s | 657 | 1811 | 0 | 0 |
| 13 | Economics | 30 | 73.33 | 126s | 1185 | 8299 | 0 | 0 |
| 14 | Electronics | 30 | 50.00 | 12.8m | 6296 | 32511 | 2 | 0 |
| 15 | Energy_and_Power | 30 | 63.33 | 40.9m | 13792 | 32565 | 8 | 2 |
| 16 | Finance | 30 | 63.33 | 11.3m | 4271 | 32390 | 2 | 0 |
| 17 | Geography | 30 | 56.67 | 10.9m | 3299 | 32534 | 2 | 0 |
| 18 | History | 30 | 70.00 | 503s | 1741 | 31085 | 1 | 0 |
| 19 | Literature | 30 | 76.67 | 517s | 1496 | 32562 | 1 | 1 |
| 20 | Manage | 30 | 73.33 | 168s | 1191 | 11273 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 124s | 1498 | 7381 | 0 | 0 |
| 22 | Materials | 30 | 66.67 | 30.2m | 11236 | 32596 | 7 | 0 |
| 23 | Math | 30 | 63.33 | 274s | 2975 | 15302 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 50.00 | 23.4m | 9687 | 32515 | 5 | 0 |
| 25 | Music | 30 | 26.67 | 14.2m | 4079 | 32366 | 3 | 1 |
| 26 | Pharmacy | 30 | 70.00 | 527s | 2101 | 32594 | 1 | 0 |
| 27 | Physics | 30 | 70.00 | 527s | 2262 | 32596 | 1 | 0 |
| 28 | Psychology | 30 | 73.33 | 59s | 722 | 3601 | 0 | 0 |
| 29 | Public_Health | 30 | 93.33 | 543s | 2637 | 32430 | 1 | 0 |
| 30 | Sociology | 30 | 60.00 | 29s | 466 | 1553 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **63.67** | 290.8m |  |  | 49 | 5 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 63.67%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 63.67 |
| 차이 (Δ) | -3.73 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 851, 'length': 49}` → length(잘림) 49건 중 오답 36건
- 파싱 실패(prediction=None): 5건, 실행 오류: 0건
- completion tokens 전체: mean 3458 / median 564 / p90 9936 / p99 32547 / max 32596
- completion tokens 정답: median 512 (mean 2263) vs 오답: median 760 (mean 5552)
- prompt tokens: mean 631 / max 5653
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 272, 'B': 200, 'C': 191, 'D': 156, 'E': 20, 'F': 2, 'I': 1, None: 5}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 65.05 |
| open | 53 | 41.51 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 61.32 |
| Easy | 295 | 73.22 |
| Hard | 181 | 53.59 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 63.23 |
| ['Tables'] | 170 | 77.06 |
| ['Plots and Charts'] | 78 | 66.67 |
| ['Photographs'] | 75 | 64.00 |
| ['Paintings'] | 46 | 63.04 |
| ['Chemical Structures'] | 30 | 33.33 |
| ['Sheet Music'] | 30 | 26.67 |
| ['Medical Images'] | 21 | 57.14 |
| ['Microscopic Images'] | 20 | 55.00 |
| ['Comics and Cartoons'] | 19 | 68.42 |
| ['Geometric Shapes'] | 17 | 64.71 |
| ['Technical Blueprints'] | 14 | 50.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Materials_1 | Materials | 32596 | length | False |
| validation_Physics_29 | Physics | 32596 | length | False |
| validation_Pharmacy_24 | Pharmacy | 32594 | length | False |
| validation_Accounting_9 | Accounting | 32583 | length | False |
| validation_Accounting_22 | Accounting | 32574 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 32565 | length | False |
| validation_Literature_10 | Literature | 32562 | length | False |
| validation_Materials_6 | Materials | 32554 | length | True |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32547 | length | True |
| validation_Geography_1 | Geography | 32534 | length | True |
