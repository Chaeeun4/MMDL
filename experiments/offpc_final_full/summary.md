# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.79 GB |
| 총 소요 시간 | 13878 s (3.85 h) 전체 / 추론 13779 s / 모델 로드 99 s |
| 실행 시각 | 2026-11-17T01:40:52+09:00 → 2026-11-17T05:32:10+09:00 |
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
| 1 | Accounting | 30 | 70.00 | 15.3m | 5683 | 32578 | 3 | 0 |
| 2 | Agriculture | 30 | 50.00 | 45s | 385 | 760 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 53.33 | 34.5m | 14140 | 32542 | 6 | 1 |
| 4 | Art | 30 | 56.67 | 510s | 1341 | 32099 | 1 | 0 |
| 5 | Art_Theory | 30 | 73.33 | 503s | 1395 | 31371 | 1 | 0 |
| 6 | Basic_Medical_Science | 30 | 63.33 | 22s | 419 | 1341 | 0 | 0 |
| 7 | Biology | 30 | 50.00 | 522s | 1869 | 32320 | 1 | 0 |
| 8 | Chemistry | 30 | 40.00 | 161s | 1327 | 10476 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 63.33 | 40s | 591 | 2542 | 0 | 0 |
| 10 | Computer_Science | 30 | 56.67 | 235s | 2536 | 13539 | 0 | 0 |
| 11 | Design | 30 | 66.67 | 24s | 366 | 1504 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 33.33 | 42s | 551 | 1937 | 0 | 0 |
| 13 | Economics | 30 | 83.33 | 30s | 581 | 1807 | 0 | 0 |
| 14 | Electronics | 30 | 43.33 | 14.3m | 7850 | 32580 | 2 | 0 |
| 15 | Energy_and_Power | 30 | 66.67 | 26.2m | 10828 | 32607 | 5 | 1 |
| 16 | Finance | 30 | 76.67 | 10.8m | 3509 | 32427 | 2 | 1 |
| 17 | Geography | 30 | 53.33 | 191s | 1896 | 11584 | 0 | 0 |
| 18 | History | 30 | 73.33 | 51s | 633 | 3266 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 517s | 1456 | 32599 | 1 | 1 |
| 20 | Manage | 30 | 73.33 | 159s | 1438 | 9728 | 0 | 0 |
| 21 | Marketing | 30 | 90.00 | 527s | 2250 | 31761 | 1 | 0 |
| 22 | Materials | 30 | 66.67 | 13.0m | 7081 | 32371 | 2 | 0 |
| 23 | Math | 30 | 63.33 | 581s | 3391 | 32464 | 1 | 0 |
| 24 | Mechanical_Engineering | 30 | 56.67 | 20.8m | 8576 | 32557 | 4 | 0 |
| 25 | Music | 30 | 33.33 | 522s | 1485 | 32609 | 1 | 0 |
| 26 | Pharmacy | 30 | 73.33 | 106s | 1221 | 6826 | 0 | 0 |
| 27 | Physics | 30 | 70.00 | 197s | 1948 | 11906 | 0 | 0 |
| 28 | Psychology | 30 | 73.33 | 507s | 1394 | 31810 | 1 | 0 |
| 29 | Public_Health | 30 | 83.33 | 156s | 1654 | 9586 | 0 | 0 |
| 30 | Sociology | 30 | 66.67 | 17s | 382 | 692 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **63.44** | 229.3m |  |  | 32 | 4 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 63.44%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 63.44 |
| 차이 (Δ) | -3.96 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 868, 'length': 32}` → length(잘림) 32건 중 오답 24건
- 파싱 실패(prediction=None): 4건, 실행 오류: 0건
- completion tokens 전체: mean 2939 / median 448 / p90 8835 / p99 32564 / max 32609
- completion tokens 정답: median 421 (mean 1986) vs 오답: median 519 (mean 4593)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 258, 'B': 198, 'C': 203, 'D': 156, 'E': 26, 'F': 1, 'I': 1, None: 4}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 65.53 |
| open | 53 | 30.19 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 61.56 |
| Easy | 295 | 73.90 |
| Hard | 181 | 50.83 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 59.19 |
| ['Tables'] | 170 | 78.82 |
| ['Plots and Charts'] | 78 | 73.08 |
| ['Photographs'] | 75 | 61.33 |
| ['Paintings'] | 46 | 56.52 |
| ['Chemical Structures'] | 30 | 36.67 |
| ['Sheet Music'] | 30 | 33.33 |
| ['Medical Images'] | 21 | 57.14 |
| ['Microscopic Images'] | 20 | 60.00 |
| ['Comics and Cartoons'] | 19 | 78.95 |
| ['Geometric Shapes'] | 17 | 82.35 |
| ['Technical Blueprints'] | 14 | 50.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_9 | Music | 32609 | length | False |
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | True |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | False |
| validation_Literature_10 | Literature | 32599 | length | False |
| validation_Electronics_1 | Electronics | 32580 | length | True |
| validation_Accounting_17 | Accounting | 32578 | length | False |
| validation_Accounting_20 | Accounting | 32569 | length | False |
| validation_Electronics_10 | Electronics | 32566 | length | False |
| validation_Energy_and_Power_26 | Energy_and_Power | 32564 | length | False |
| validation_Mechanical_Engineering_8 | Mechanical_Engineering | 32557 | length | False |
