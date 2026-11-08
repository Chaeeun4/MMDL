# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.72 GB |
| 총 소요 시간 | 10467 s (2.91 h) 전체 / 추론 10363 s / 모델 로드 104 s |
| 실행 시각 | 2026-11-04T20:47:38+09:00 → 2026-11-04T23:42:05+09:00 |
| git | `jina` @ `024ea1798f8f03ec8b8cbb5ce2197e7f580cfb32` dirty=True |

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
| 1 | Accounting | 30 | 80.00 | 14.9m | 5035 | 32574 | 3 | 0 |
| 2 | Agriculture | 30 | 46.67 | 35s | 164 | 442 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 66.67 | 22.9m | 9856 | 32547 | 4 | 0 |
| 4 | Art | 30 | 66.67 | 508s | 1186 | 32062 | 1 | 0 |
| 5 | Art_Theory | 30 | 80.00 | 47s | 257 | 3058 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 12s | 179 | 750 | 0 | 0 |
| 7 | Biology | 30 | 40.00 | 68s | 386 | 4660 | 0 | 0 |
| 8 | Chemistry | 30 | 40.00 | 158s | 1630 | 9853 | 0 | 1 |
| 9 | Clinical_Medicine | 30 | 70.00 | 35s | 366 | 2403 | 0 | 0 |
| 10 | Computer_Science | 30 | 56.67 | 173s | 1381 | 10939 | 0 | 0 |
| 11 | Design | 30 | 76.67 | 11s | 176 | 514 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 26.67 | 38s | 410 | 1713 | 0 | 0 |
| 13 | Economics | 30 | 66.67 | 98s | 576 | 6993 | 0 | 0 |
| 14 | Electronics | 30 | 43.33 | 11.4m | 5169 | 32558 | 1 | 0 |
| 15 | Energy_and_Power | 30 | 60.00 | 28.8m | 11261 | 32524 | 6 | 0 |
| 16 | Finance | 30 | 60.00 | 14.5m | 4085 | 32472 | 3 | 0 |
| 17 | Geography | 30 | 46.67 | 158s | 1505 | 9624 | 0 | 0 |
| 18 | History | 30 | 73.33 | 40s | 297 | 2647 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 515s | 1319 | 32562 | 1 | 1 |
| 20 | Manage | 30 | 60.00 | 114s | 943 | 7659 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 171s | 971 | 11611 | 0 | 0 |
| 22 | Materials | 30 | 70.00 | 11.8m | 6484 | 32334 | 1 | 0 |
| 23 | Math | 30 | 56.67 | 335s | 2520 | 19510 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 63.33 | 13.1m | 6108 | 32454 | 2 | 0 |
| 25 | Music | 30 | 36.67 | 532s | 1998 | 32604 | 1 | 0 |
| 26 | Pharmacy | 30 | 73.33 | 44s | 445 | 3004 | 0 | 0 |
| 27 | Physics | 30 | 76.67 | 77s | 756 | 5198 | 0 | 0 |
| 28 | Psychology | 30 | 76.67 | 14s | 155 | 690 | 0 | 0 |
| 29 | Public_Health | 30 | 83.33 | 114s | 948 | 7648 | 0 | 0 |
| 30 | Sociology | 30 | 73.33 | 13s | 222 | 424 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **63.56** | 172.4m |  |  | 23 | 2 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 63.56%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 63.56 |
| 차이 (Δ) | -3.84 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 877, 'length': 23}` → length(잘림) 23건 중 오답 15건
- 파싱 실패(prediction=None): 2건, 실행 오류: 0건
- completion tokens 전체: mean 2226 / median 210 / p90 6566 / p99 32489 / max 32604
- completion tokens 정답: median 194 (mean 1597) vs 오답: median 252 (mean 3324)
- prompt tokens: mean 631 / max 5653
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 255, 'B': 223, 'C': 194, 'D': 155, 'E': 16, 'I': 2, None: 2}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 65.41 |
| open | 53 | 33.96 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 60.38 |
| Easy | 295 | 72.20 |
| Hard | 181 | 56.91 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 63.68 |
| ['Tables'] | 170 | 78.24 |
| ['Plots and Charts'] | 78 | 60.26 |
| ['Photographs'] | 75 | 65.33 |
| ['Paintings'] | 46 | 71.74 |
| ['Chemical Structures'] | 30 | 33.33 |
| ['Sheet Music'] | 30 | 36.67 |
| ['Medical Images'] | 21 | 52.38 |
| ['Microscopic Images'] | 20 | 65.00 |
| ['Comics and Cartoons'] | 19 | 63.16 |
| ['Geometric Shapes'] | 17 | 58.82 |
| ['Technical Blueprints'] | 14 | 57.14 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_28 | Music | 32604 | length | False |
| validation_Accounting_22 | Accounting | 32574 | length | True |
| validation_Literature_10 | Literature | 32562 | length | False |
| validation_Electronics_18 | Electronics | 32558 | length | True |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32547 | length | True |
| validation_Accounting_20 | Accounting | 32532 | length | False |
| validation_Energy_and_Power_30 | Energy_and_Power | 32524 | length | False |
| validation_Accounting_2 | Accounting | 32522 | length | False |
| validation_Architecture_and_Engineering_9 | Architecture_and_Engineering | 32489 | length | True |
| validation_Energy_and_Power_1 | Energy_and_Power | 32489 | length | False |
