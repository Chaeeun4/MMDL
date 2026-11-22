# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.55 GB |
| 총 소요 시간 | 20014 s (5.56 h) 전체 / 추론 19908 s / 모델 로드 106 s |
| 실행 시각 | 2026-11-22T02:11:02+09:00 → 2026-11-22T07:44:37+09:00 |
| git | `jina` @ `156d954325ddf08a959b3d62af6fa91bd7bcd46a` dirty=True |

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
| 1 | Accounting | 30 | 76.67 | 24.7m | 8044 | 32611 | 6 | 0 |
| 2 | Agriculture | 30 | 53.33 | 47s | 388 | 803 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 63.33 | 29.7m | 12880 | 32542 | 5 | 0 |
| 4 | Art | 30 | 63.33 | 512s | 1445 | 32099 | 1 | 0 |
| 5 | Art_Theory | 30 | 70.00 | 28s | 465 | 1391 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 73.33 | 28s | 424 | 1847 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 129s | 1334 | 7770 | 0 | 0 |
| 8 | Chemistry | 30 | 46.67 | 124s | 2342 | 6733 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 63.33 | 517s | 1661 | 32476 | 1 | 0 |
| 10 | Computer_Science | 30 | 73.33 | 543s | 2778 | 32501 | 1 | 1 |
| 11 | Design | 30 | 76.67 | 16s | 346 | 846 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 26.67 | 57s | 780 | 2603 | 0 | 0 |
| 13 | Economics | 30 | 83.33 | 98s | 1136 | 6375 | 0 | 0 |
| 14 | Electronics | 30 | 50.00 | 19.2m | 8145 | 32581 | 4 | 0 |
| 15 | Energy_and_Power | 30 | 50.00 | 49.7m | 16884 | 32607 | 13 | 4 |
| 16 | Finance | 30 | 70.00 | 548s | 2950 | 32368 | 1 | 0 |
| 17 | Geography | 30 | 50.00 | 217s | 1930 | 13131 | 0 | 0 |
| 18 | History | 30 | 73.33 | 519s | 1866 | 32084 | 1 | 0 |
| 19 | Literature | 30 | 83.33 | 517s | 1429 | 32599 | 1 | 1 |
| 20 | Manage | 30 | 70.00 | 168s | 1410 | 11201 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 105s | 1082 | 6769 | 0 | 0 |
| 22 | Materials | 30 | 43.33 | 37.3m | 13697 | 32591 | 9 | 0 |
| 23 | Math | 30 | 73.33 | 594s | 4059 | 32006 | 1 | 0 |
| 24 | Mechanical_Engineering | 30 | 53.33 | 26.6m | 10355 | 32580 | 6 | 0 |
| 25 | Music | 30 | 23.33 | 30.8m | 9633 | 32644 | 8 | 1 |
| 26 | Pharmacy | 30 | 73.33 | 10.6m | 2848 | 32631 | 2 | 0 |
| 27 | Physics | 30 | 70.00 | 173s | 1496 | 11630 | 0 | 0 |
| 28 | Psychology | 30 | 76.67 | 70s | 755 | 4457 | 0 | 0 |
| 29 | Public_Health | 30 | 86.67 | 11.0m | 3663 | 32467 | 2 | 0 |
| 30 | Sociology | 30 | 56.67 | 510s | 1447 | 31910 | 1 | 1 |
|  | **Overall (macro avg)** | **900** | **63.78** | 331.5m |  |  | 63 | 8 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 63.78%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 63.78 |
| 차이 (Δ) | -3.62 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 837, 'length': 63}` → length(잘림) 63건 중 오답 48건
- 파싱 실패(prediction=None): 8건, 실행 오류: 0건
- completion tokens 전체: mean 3922 / median 565 / p90 11154 / p99 32591 / max 32644
- completion tokens 정답: median 456 (mean 2198) vs 오답: median 1140 (mean 6959)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 242, 'B': 199, 'C': 207, 'D': 166, 'E': 22, 'F': 1, 'H': 1, 'I': 1, None: 8}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 65.05 |
| open | 53 | 43.40 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 62.50 |
| Easy | 295 | 73.56 |
| Hard | 181 | 50.83 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 59.19 |
| ['Tables'] | 170 | 80.59 |
| ['Plots and Charts'] | 78 | 67.95 |
| ['Photographs'] | 75 | 58.67 |
| ['Paintings'] | 46 | 60.87 |
| ['Chemical Structures'] | 30 | 36.67 |
| ['Sheet Music'] | 30 | 23.33 |
| ['Medical Images'] | 21 | 76.19 |
| ['Microscopic Images'] | 20 | 75.00 |
| ['Comics and Cartoons'] | 19 | 78.95 |
| ['Geometric Shapes'] | 17 | 76.47 |
| ['Technical Blueprints'] | 14 | 64.29 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_8 | Music | 32644 | length | False |
| validation_Music_28 | Music | 32641 | length | True |
| validation_Pharmacy_24 | Pharmacy | 32631 | length | True |
| validation_Music_22 | Music | 32625 | length | False |
| validation_Accounting_22 | Accounting | 32611 | length | True |
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | True |
| validation_Literature_10 | Literature | 32599 | length | False |
| validation_Materials_6 | Materials | 32591 | length | True |
| validation_Electronics_5 | Electronics | 32581 | length | False |
