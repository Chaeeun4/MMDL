# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.50 GB |
| 총 소요 시간 | 9212 s (2.56 h) 전체 / 추론 9114 s / 모델 로드 97 s |
| 실행 시각 | 2026-11-15T09:07:05+09:00 → 2026-11-15T11:40:37+09:00 |
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
| 1 | Accounting | 30 | 73.33 | 11.1m | 4057 | 32611 | 2 | 0 |
| 2 | Agriculture | 30 | 56.67 | 26s | 9 | 24 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 63.33 | 21.1m | 10578 | 32526 | 3 | 1 |
| 4 | Art | 30 | 70.00 | 4s | 7 | 17 | 0 | 0 |
| 5 | Art_Theory | 30 | 70.00 | 5s | 6 | 14 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 11s | 32 | 741 | 0 | 0 |
| 7 | Biology | 30 | 46.67 | 98s | 526 | 6747 | 0 | 0 |
| 8 | Chemistry | 30 | 40.00 | 222s | 1435 | 14744 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 66.67 | 11s | 97 | 664 | 0 | 0 |
| 10 | Computer_Science | 30 | 50.00 | 210s | 1332 | 13104 | 0 | 0 |
| 11 | Design | 30 | 80.00 | 3s | 7 | 19 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 30.00 | 10s | 6 | 17 | 0 | 0 |
| 13 | Economics | 30 | 70.00 | 126s | 813 | 8886 | 0 | 0 |
| 14 | Electronics | 30 | 43.33 | 567s | 2743 | 32546 | 1 | 0 |
| 15 | Energy_and_Power | 30 | 66.67 | 17.0m | 8372 | 32602 | 3 | 1 |
| 16 | Finance | 30 | 60.00 | 10.8m | 3255 | 32427 | 2 | 1 |
| 17 | Geography | 30 | 56.67 | 534s | 1797 | 32571 | 1 | 0 |
| 18 | History | 30 | 70.00 | 13s | 33 | 676 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 8s | 16 | 338 | 0 | 0 |
| 20 | Manage | 30 | 43.33 | 170s | 705 | 11932 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 148s | 940 | 10062 | 0 | 0 |
| 22 | Materials | 30 | 50.00 | 24.5m | 9936 | 32633 | 5 | 0 |
| 23 | Math | 30 | 60.00 | 215s | 2020 | 13182 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 56.67 | 12.6m | 6028 | 32409 | 2 | 0 |
| 25 | Music | 30 | 26.67 | 10.6m | 2349 | 32609 | 2 | 0 |
| 26 | Pharmacy | 30 | 66.67 | 12s | 141 | 818 | 0 | 0 |
| 27 | Physics | 30 | 70.00 | 76s | 1042 | 4972 | 0 | 0 |
| 28 | Psychology | 30 | 66.67 | 13s | 102 | 595 | 0 | 0 |
| 29 | Public_Health | 30 | 90.00 | 150s | 1296 | 9602 | 0 | 0 |
| 30 | Sociology | 30 | 53.33 | 9s | 16 | 314 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **61.11** | 151.6m |  |  | 21 | 3 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 61.11%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 61.11 |
| 차이 (Δ) | -6.29 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 879, 'length': 21}` → length(잘림) 21건 중 오답 16건
- 파싱 실패(prediction=None): 3건, 실행 오류: 0건
- completion tokens 전체: mean 1990 / median 10 / p90 6082 / p99 32520 / max 32633
- completion tokens 정답: median 14 (mean 1523) vs 오답: median 8 (mean 2724)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 238, 'B': 187, 'C': 253, 'D': 144, 'E': 19, 'F': 3, None: 3}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 64.11 |
| open | 53 | 13.21 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 57.78 |
| Easy | 295 | 69.49 |
| Hard | 181 | 55.25 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 62.78 |
| ['Tables'] | 170 | 75.88 |
| ['Plots and Charts'] | 78 | 52.56 |
| ['Photographs'] | 75 | 61.33 |
| ['Paintings'] | 46 | 60.87 |
| ['Chemical Structures'] | 30 | 30.00 |
| ['Sheet Music'] | 30 | 26.67 |
| ['Medical Images'] | 21 | 52.38 |
| ['Microscopic Images'] | 20 | 65.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 70.59 |
| ['Technical Blueprints'] | 14 | 35.71 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Materials_1 | Materials | 32633 | length | False |
| validation_Accounting_22 | Accounting | 32611 | length | True |
| validation_Music_9 | Music | 32609 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | False |
| validation_Geography_1 | Geography | 32571 | length | False |
| validation_Electronics_28 | Electronics | 32546 | length | True |
| validation_Architecture_and_Engineering_9 | Architecture_and_Engineering | 32526 | length | True |
| validation_Energy_and_Power_1 | Energy_and_Power | 32526 | length | False |
| validation_Materials_9 | Materials | 32520 | length | False |
| validation_Architecture_and_Engineering_13 | Architecture_and_Engineering | 32503 | length | False |
