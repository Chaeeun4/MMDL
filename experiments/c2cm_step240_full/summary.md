# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.50 GB |
| 총 소요 시간 | 5604 s (1.56 h) 전체 / 추론 5501 s / 모델 로드 103 s |
| 실행 시각 | 2026-11-23T21:32:52+09:00 → 2026-11-23T23:06:16+09:00 |
| git | `jina` @ `ec3965651a8e1fafd1cc981f2138896ae0ffe796` dirty=True |

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
| 1 | Accounting | 30 | 70.00 | 241s | 2566 | 13094 | 0 | 0 |
| 2 | Agriculture | 30 | 56.67 | 25s | 8 | 24 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 43.33 | 14.3m | 7626 | 32507 | 2 | 0 |
| 4 | Art | 30 | 66.67 | 4s | 5 | 13 | 0 | 0 |
| 5 | Art_Theory | 30 | 70.00 | 5s | 4 | 14 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 11s | 36 | 788 | 0 | 0 |
| 7 | Biology | 30 | 50.00 | 68s | 514 | 4524 | 0 | 0 |
| 8 | Chemistry | 30 | 40.00 | 113s | 1034 | 7247 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 63.33 | 10s | 48 | 610 | 0 | 0 |
| 10 | Computer_Science | 30 | 50.00 | 84s | 533 | 5786 | 0 | 0 |
| 11 | Design | 30 | 76.67 | 3s | 5 | 19 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 40.00 | 10s | 3 | 17 | 0 | 0 |
| 13 | Economics | 30 | 73.33 | 107s | 629 | 7649 | 0 | 0 |
| 14 | Electronics | 30 | 46.67 | 184s | 1491 | 11548 | 0 | 0 |
| 15 | Energy_and_Power | 30 | 73.33 | 16.1m | 7205 | 32607 | 3 | 0 |
| 16 | Finance | 30 | 63.33 | 177s | 1747 | 10604 | 0 | 0 |
| 17 | Geography | 30 | 53.33 | 146s | 650 | 10345 | 0 | 0 |
| 18 | History | 30 | 70.00 | 10s | 33 | 463 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 6s | 10 | 182 | 0 | 0 |
| 20 | Manage | 30 | 43.33 | 114s | 637 | 7688 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 163s | 874 | 11345 | 0 | 0 |
| 22 | Materials | 30 | 53.33 | 16.9m | 7984 | 32371 | 3 | 0 |
| 23 | Math | 30 | 66.67 | 185s | 2037 | 10619 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 43.33 | 11.1m | 5101 | 32552 | 1 | 0 |
| 25 | Music | 30 | 33.33 | 73s | 180 | 5297 | 0 | 0 |
| 26 | Pharmacy | 30 | 63.33 | 11s | 93 | 739 | 0 | 0 |
| 27 | Physics | 30 | 60.00 | 100s | 819 | 7052 | 0 | 0 |
| 28 | Psychology | 30 | 73.33 | 11s | 69 | 480 | 0 | 0 |
| 29 | Public_Health | 30 | 86.67 | 113s | 1215 | 6991 | 0 | 0 |
| 30 | Sociology | 30 | 56.67 | 5s | 4 | 25 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **60.78** | 91.4m |  |  | 9 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 60.78%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 60.78 |
| 차이 (Δ) | -6.62 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 891, 'length': 9}` → length(잘림) 9건 중 오답 5건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 1439 / median 8 / p90 4657 / p99 32236 / max 32607
- completion tokens 정답: median 9 (mean 1165) vs 오답: median 6 (mean 1863)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 242, 'B': 187, 'C': 248, 'D': 144, 'E': 23, 'F': 2, 'I': 1}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 63.52 |
| open | 53 | 16.98 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 58.96 |
| Easy | 295 | 69.83 |
| Hard | 181 | 50.28 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 58.30 |
| ['Tables'] | 170 | 73.53 |
| ['Plots and Charts'] | 78 | 57.69 |
| ['Photographs'] | 75 | 61.33 |
| ['Paintings'] | 46 | 60.87 |
| ['Chemical Structures'] | 30 | 40.00 |
| ['Sheet Music'] | 30 | 33.33 |
| ['Medical Images'] | 21 | 57.14 |
| ['Microscopic Images'] | 20 | 65.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 76.47 |
| ['Technical Blueprints'] | 14 | 42.86 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | True |
| validation_Mechanical_Engineering_23 | Mechanical_Engineering | 32552 | length | True |
| validation_Architecture_and_Engineering_17 | Architecture_and_Engineering | 32507 | length | False |
| validation_Energy_and_Power_20 | Energy_and_Power | 32495 | length | True |
| validation_Architecture_and_Engineering_20 | Architecture_and_Engineering | 32383 | length | False |
| validation_Materials_3 | Materials | 32371 | length | False |
| validation_Materials_13 | Materials | 32349 | length | False |
| validation_Energy_and_Power_12 | Energy_and_Power | 32290 | length | True |
| validation_Materials_11 | Materials | 32236 | length | False |
| validation_Materials_9 | Materials | 19866 | stop | False |
