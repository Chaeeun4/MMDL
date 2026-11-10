# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 4090 (24 GB) (host `AIX408-7`, driver 535.183.01, CUDA 12.8) |
| 실측 peak VRAM | 21.89 GB |
| 총 소요 시간 | 12148 s (3.37 h) 전체 / 추론 12072 s / 모델 로드 76 s |
| 실행 시각 | 2026-10-05T17:05:39+09:00 → 2026-10-05T20:28:07+09:00 |
| git | `main` @ `fe18b1ad5e90e38005db3b02dac4bce39e6e6c09` dirty=True |

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
| 1 | Accounting | 30 | 73.33 | 559s | 4441 | 16188 | 6 | 0 |
| 2 | Agriculture | 30 | 50.00 | 48s | 378 | 1325 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 40.00 | 21.2m | 10460 | 16118 | 14 | 1 |
| 4 | Art | 30 | 56.67 | 231s | 1360 | 15675 | 2 | 1 |
| 5 | Art_Theory | 30 | 80.00 | 183s | 921 | 15446 | 1 | 1 |
| 6 | Basic_Medical_Science | 30 | 73.33 | 45s | 494 | 2664 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 205s | 1567 | 16194 | 1 | 0 |
| 8 | Chemistry | 30 | 50.00 | 560s | 4768 | 16223 | 7 | 0 |
| 9 | Clinical_Medicine | 30 | 73.33 | 261s | 1703 | 16217 | 2 | 0 |
| 10 | Computer_Science | 30 | 56.67 | 213s | 2125 | 9998 | 0 | 0 |
| 11 | Design | 30 | 70.00 | 202s | 844 | 15805 | 1 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 30.00 | 197s | 1108 | 16192 | 1 | 0 |
| 13 | Economics | 30 | 76.67 | 230s | 1495 | 15835 | 1 | 0 |
| 14 | Electronics | 30 | 43.33 | 14.0m | 7260 | 16219 | 8 | 0 |
| 15 | Energy_and_Power | 30 | 53.33 | 19.2m | 8998 | 16179 | 13 | 2 |
| 16 | Finance | 30 | 83.33 | 435s | 3345 | 16003 | 2 | 0 |
| 17 | Geography | 30 | 56.67 | 283s | 2512 | 16175 | 3 | 0 |
| 18 | History | 30 | 66.67 | 226s | 1082 | 15751 | 1 | 0 |
| 19 | Literature | 30 | 86.67 | 41s | 349 | 2083 | 0 | 0 |
| 20 | Manage | 30 | 66.67 | 311s | 2474 | 15960 | 2 | 0 |
| 21 | Marketing | 30 | 86.67 | 221s | 1218 | 15492 | 1 | 0 |
| 22 | Materials | 30 | 60.00 | 17.5m | 8598 | 16167 | 11 | 1 |
| 23 | Math | 30 | 63.33 | 491s | 3649 | 16115 | 2 | 0 |
| 24 | Mechanical_Engineering | 30 | 46.67 | 14.4m | 7049 | 16181 | 10 | 1 |
| 25 | Music | 30 | 43.33 | 13.6m | 6323 | 16222 | 11 | 0 |
| 26 | Pharmacy | 30 | 83.33 | 255s | 1957 | 16129 | 2 | 0 |
| 27 | Physics | 30 | 80.00 | 207s | 1708 | 16169 | 1 | 0 |
| 28 | Psychology | 30 | 76.67 | 196s | 1085 | 15650 | 1 | 0 |
| 29 | Public_Health | 30 | 86.67 | 274s | 1891 | 15934 | 1 | 1 |
| 30 | Sociology | 30 | 66.67 | 203s | 870 | 15486 | 1 | 0 |
|  | **Overall (macro avg)** | **900** | **64.44** | 201.1m |  |  | 106 | 8 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 64.44%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 64.44 |
| 차이 (Δ) | -2.96 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'length': 106, 'stop': 794}` → length(잘림) 106건 중 오답 73건
- 파싱 실패(prediction=None): 8건, 실행 오류: 0건
- completion tokens 전체: mean 3068 / median 510 / p90 15718 / p99 16206 / max 16223
- completion tokens 정답: median 424 (mean 1961) vs 오답: median 950 (mean 5074)
- prompt tokens: mean 634 / max 5656
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 262, 'B': 215, 'C': 170, 'D': 170, 'E': 19, 'F': 1, 'I': 2, None: 8}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 65.76 |
| open | 53 | 43.40 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 63.92 |
| Easy | 295 | 73.90 |
| Hard | 181 | 50.28 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 59.64 |
| ['Tables'] | 170 | 80.00 |
| ['Plots and Charts'] | 78 | 69.23 |
| ['Photographs'] | 75 | 62.67 |
| ['Paintings'] | 46 | 67.39 |
| ['Chemical Structures'] | 30 | 40.00 |
| ['Sheet Music'] | 30 | 43.33 |
| ['Medical Images'] | 21 | 71.43 |
| ['Microscopic Images'] | 20 | 60.00 |
| ['Comics and Cartoons'] | 19 | 68.42 |
| ['Geometric Shapes'] | 17 | 70.59 |
| ['Technical Blueprints'] | 14 | 50.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Chemistry_20 | Chemistry | 16223 | length | False |
| validation_Music_3 | Music | 16222 | length | False |
| validation_Electronics_29 | Electronics | 16219 | length | False |
| validation_Music_15 | Music | 16219 | length | True |
| validation_Clinical_Medicine_26 | Clinical_Medicine | 16217 | length | True |
| validation_Music_28 | Music | 16217 | length | True |
| validation_Chemistry_7 | Chemistry | 16211 | length | False |
| validation_Clinical_Medicine_15 | Clinical_Medicine | 16207 | length | True |
| validation_Electronics_11 | Electronics | 16206 | length | False |
| validation_Biology_4 | Biology | 16194 | length | False |

## 다른 run과의 비교

- 비교 대상 overall: 61.11% (Δ +3.33p)
- 정오답 전이 (this → other): `{'C->C': 466, 'W->C': 84, 'W->W': 236, 'C->W': 114}`
