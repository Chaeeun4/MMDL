# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM ? (torch ?, transformers ?, qwen-vl-utils ?) |
| 사용 GPU | ? (host `?`, driver ?, CUDA ?) |
| 실측 peak VRAM | - |
| 실행 시각 | None → None |
| git | `None` @ `None` dirty=None |

## 생성 설정

| 파라미터 | 값 |
|---|---|
| `greedy` | None |
| `seed` | None |
| `temperature` | None |
| `top_p` | None |
| `top_k` | None |
| `repetition_penalty` | None |
| `presence_penalty` | None |
| `max_new_tokens` | None |
| `logprobs` | None |
| `min_pixels` | None |
| `max_pixels` | None |
| 공식 recipe 일치 | None |

## 결과

| No. | Subject | Data Num | Acc | 소요 시간 | 평균 토큰 | 최대 토큰 | length stop | parse 실패 |
|---|---|---|---|---|---|---|---|---|
| 1 | Accounting | 30 | 66.67 | - | 4441 | 16188 | 6 | 6 |
| 2 | Agriculture | 30 | 50.00 | - | 378 | 1325 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 33.33 | - | 10460 | 16118 | 14 | 14 |
| 4 | Art | 30 | 56.67 | - | 1360 | 15675 | 2 | 2 |
| 5 | Art_Theory | 30 | 80.00 | - | 921 | 15446 | 1 | 1 |
| 6 | Basic_Medical_Science | 30 | 73.33 | - | 494 | 2664 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | - | 1567 | 16194 | 1 | 1 |
| 8 | Chemistry | 30 | 40.00 | - | 4768 | 16223 | 7 | 4 |
| 9 | Clinical_Medicine | 30 | 66.67 | - | 1703 | 16217 | 2 | 2 |
| 10 | Computer_Science | 30 | 56.67 | - | 2125 | 9998 | 0 | 0 |
| 11 | Design | 30 | 70.00 | - | 844 | 15805 | 1 | 1 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 30.00 | - | 1108 | 16192 | 1 | 1 |
| 13 | Economics | 30 | 73.33 | - | 1495 | 15835 | 1 | 1 |
| 14 | Electronics | 30 | 43.33 | - | 7260 | 16219 | 8 | 5 |
| 15 | Energy_and_Power | 30 | 43.33 | - | 8998 | 16179 | 13 | 14 |
| 16 | Finance | 30 | 76.67 | - | 3345 | 16003 | 2 | 2 |
| 17 | Geography | 30 | 46.67 | - | 2512 | 16175 | 3 | 3 |
| 18 | History | 30 | 66.67 | - | 1082 | 15751 | 1 | 1 |
| 19 | Literature | 30 | 86.67 | - | 349 | 2083 | 0 | 0 |
| 20 | Manage | 30 | 60.00 | - | 2474 | 15960 | 2 | 2 |
| 21 | Marketing | 30 | 86.67 | - | 1218 | 15492 | 1 | 1 |
| 22 | Materials | 30 | 43.33 | - | 8598 | 16167 | 11 | 11 |
| 23 | Math | 30 | 56.67 | - | 3649 | 16115 | 2 | 3 |
| 24 | Mechanical_Engineering | 30 | 40.00 | - | 7049 | 16181 | 10 | 11 |
| 25 | Music | 30 | 30.00 | - | 6323 | 16222 | 11 | 11 |
| 26 | Pharmacy | 30 | 76.67 | - | 1957 | 16129 | 2 | 1 |
| 27 | Physics | 30 | 80.00 | - | 1708 | 16169 | 1 | 1 |
| 28 | Psychology | 30 | 76.67 | - | 1085 | 15650 | 1 | 1 |
| 29 | Public_Health | 30 | 86.67 | - | 1891 | 15934 | 1 | 1 |
| 30 | Sociology | 30 | 66.67 | - | 870 | 15486 | 1 | 1 |
|  | **Overall (macro avg)** | **900** | **60.56** | 0s |  |  | 106 | 102 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 60.56%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 60.56 |
| 차이 (Δ) | -6.84 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'length': 106, 'stop': 794}` → length(잘림) 106건 중 오답 106건
- 파싱 실패(prediction=None): 102건, 실행 오류: 0건
- completion tokens 전체: mean 3068 / median 510 / p90 15718 / p99 16206 / max 16223
- completion tokens 정답: median 402 (mean 1070) vs 오답: median 1500 (mean 6135)
- prompt tokens: mean 634 / max 5656
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 230, 'B': 200, 'C': 152, 'D': 141, 'E': 19, 'F': 1, 'I': 2, None: 102}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 61.87 |
| open | 53 | 39.62 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 60.38 |
| Easy | 295 | 71.53 |
| Hard | 181 | 43.09 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 54.71 |
| ['Tables'] | 170 | 76.47 |
| ['Plots and Charts'] | 78 | 67.95 |
| ['Photographs'] | 75 | 62.67 |
| ['Paintings'] | 46 | 67.39 |
| ['Chemical Structures'] | 30 | 23.33 |
| ['Sheet Music'] | 30 | 30.00 |
| ['Medical Images'] | 21 | 71.43 |
| ['Microscopic Images'] | 20 | 60.00 |
| ['Comics and Cartoons'] | 19 | 68.42 |
| ['Geometric Shapes'] | 17 | 64.71 |
| ['Technical Blueprints'] | 14 | 50.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Chemistry_20 | Chemistry | 16223 | length | False |
| validation_Music_3 | Music | 16222 | length | False |
| validation_Electronics_29 | Electronics | 16219 | length | False |
| validation_Music_15 | Music | 16219 | length | False |
| validation_Clinical_Medicine_26 | Clinical_Medicine | 16217 | length | False |
| validation_Music_28 | Music | 16217 | length | False |
| validation_Chemistry_7 | Chemistry | 16211 | length | False |
| validation_Clinical_Medicine_15 | Clinical_Medicine | 16207 | length | False |
| validation_Electronics_11 | Electronics | 16206 | length | False |
| validation_Biology_4 | Biology | 16194 | length | False |

## 다른 run과의 비교

- 비교 대상 overall: 61.11% (Δ -0.56p)
- 정오답 전이 (this → other): `{'W->C': 103, 'C->C': 447, 'C->W': 98, 'W->W': 252}`
