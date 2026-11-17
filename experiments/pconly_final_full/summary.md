# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.50 GB |
| 총 소요 시간 | 5728 s (1.59 h) 전체 / 추론 5622 s / 모델 로드 106 s |
| 실행 시각 | 2026-11-16T22:16:04+09:00 → 2026-11-16T23:51:32+09:00 |
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
| 1 | Accounting | 30 | 60.00 | 16s | 149 | 752 | 0 | 1 |
| 2 | Agriculture | 30 | 46.67 | 28s | 58 | 118 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 30.00 | 17.2m | 4854 | 32542 | 4 | 1 |
| 4 | Art | 30 | 66.67 | 6s | 58 | 102 | 0 | 0 |
| 5 | Art_Theory | 30 | 83.33 | 7s | 61 | 133 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 60.00 | 4s | 84 | 192 | 0 | 0 |
| 7 | Biology | 30 | 40.00 | 8s | 92 | 263 | 0 | 0 |
| 8 | Chemistry | 30 | 20.00 | 6s | 108 | 305 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 43.33 | 506s | 1170 | 32073 | 1 | 1 |
| 10 | Computer_Science | 30 | 33.33 | 8s | 117 | 314 | 0 | 0 |
| 11 | Design | 30 | 73.33 | 5s | 58 | 128 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 36.67 | 13s | 93 | 181 | 0 | 0 |
| 13 | Economics | 30 | 63.33 | 6s | 100 | 316 | 0 | 0 |
| 14 | Electronics | 30 | 26.67 | 510s | 1226 | 32566 | 1 | 1 |
| 15 | Energy_and_Power | 30 | 50.00 | 521s | 1592 | 32570 | 1 | 0 |
| 16 | Finance | 30 | 46.67 | 511s | 1273 | 32509 | 1 | 2 |
| 17 | Geography | 30 | 43.33 | 6s | 88 | 220 | 0 | 0 |
| 18 | History | 30 | 76.67 | 7s | 91 | 170 | 0 | 0 |
| 19 | Literature | 30 | 83.33 | 5s | 52 | 100 | 0 | 0 |
| 20 | Manage | 30 | 50.00 | 6s | 101 | 249 | 0 | 0 |
| 21 | Marketing | 30 | 63.33 | 10.4m | 2253 | 32138 | 2 | 2 |
| 22 | Materials | 30 | 43.33 | 10.5m | 2317 | 32544 | 2 | 1 |
| 23 | Math | 30 | 60.00 | 29s | 212 | 2059 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 40.00 | 10.6m | 2638 | 32447 | 2 | 0 |
| 25 | Music | 30 | 36.67 | 445s | 1031 | 27152 | 1 | 0 |
| 26 | Pharmacy | 30 | 46.67 | 5s | 102 | 262 | 0 | 0 |
| 27 | Physics | 30 | 63.33 | 9s | 119 | 555 | 0 | 0 |
| 28 | Psychology | 30 | 70.00 | 7s | 83 | 166 | 0 | 0 |
| 29 | Public_Health | 30 | 60.00 | 8s | 111 | 500 | 0 | 0 |
| 30 | Sociology | 30 | 76.67 | 8s | 72 | 186 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **53.11** | 93.4m |  |  | 15 | 9 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 53.11%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 53.11 |
| 차이 (Δ) | -14.29 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 885, 'length': 15}` → length(잘림) 15건 중 오답 13건
- 파싱 실패(prediction=None): 9건, 실행 오류: 0건
- completion tokens 전체: mean 679 / median 87 / p90 220 / p99 32409 / max 32570
- completion tokens 정답: median 77 (mean 264) vs 오답: median 105 (mean 1149)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 269, 'B': 231, 'C': 168, 'D': 146, 'E': 23, 'F': 1, None: 9}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 55.61 |
| open | 53 | 13.21 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 50.24 |
| Easy | 295 | 67.12 |
| Hard | 181 | 37.02 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 46.64 |
| ['Tables'] | 170 | 52.94 |
| ['Plots and Charts'] | 78 | 55.13 |
| ['Photographs'] | 75 | 69.33 |
| ['Paintings'] | 46 | 69.57 |
| ['Chemical Structures'] | 30 | 20.00 |
| ['Sheet Music'] | 30 | 36.67 |
| ['Medical Images'] | 21 | 57.14 |
| ['Microscopic Images'] | 20 | 70.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 52.94 |
| ['Technical Blueprints'] | 14 | 50.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Energy_and_Power_3 | Energy_and_Power | 32570 | length | False |
| validation_Electronics_10 | Electronics | 32566 | length | True |
| validation_Materials_14 | Materials | 32544 | length | False |
| validation_Architecture_and_Engineering_29 | Architecture_and_Engineering | 32542 | length | False |
| validation_Architecture_and_Engineering_2 | Architecture_and_Engineering | 32522 | length | True |
| validation_Architecture_and_Engineering_8 | Architecture_and_Engineering | 32509 | length | False |
| validation_Finance_28 | Finance | 32509 | length | False |
| validation_Mechanical_Engineering_28 | Mechanical_Engineering | 32447 | length | False |
| validation_Mechanical_Engineering_4 | Mechanical_Engineering | 32409 | length | False |
| validation_Materials_21 | Materials | 32366 | length | False |
