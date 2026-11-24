# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.50 GB |
| 총 소요 시간 | 14325 s (3.98 h) 전체 / 추론 14221 s / 모델 로드 103 s |
| 실행 시각 | 2026-11-24T02:51:23+09:00 → 2026-11-24T06:50:08+09:00 |
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
| 1 | Accounting | 30 | 80.00 | 11.9m | 4808 | 32611 | 2 | 0 |
| 2 | Agriculture | 30 | 50.00 | 46s | 391 | 784 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 46.67 | 29.8m | 12617 | 32584 | 5 | 0 |
| 4 | Art | 30 | 63.33 | 511s | 1403 | 32099 | 1 | 0 |
| 5 | Art_Theory | 30 | 70.00 | 512s | 1538 | 31870 | 1 | 0 |
| 6 | Basic_Medical_Science | 30 | 66.67 | 34s | 496 | 2293 | 0 | 0 |
| 7 | Biology | 30 | 36.67 | 120s | 1272 | 7497 | 0 | 0 |
| 8 | Chemistry | 30 | 46.67 | 135s | 2585 | 6983 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 63.33 | 38s | 613 | 2459 | 0 | 0 |
| 10 | Computer_Science | 30 | 70.00 | 197s | 2503 | 10926 | 0 | 0 |
| 11 | Design | 30 | 80.00 | 36s | 443 | 2386 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 20.00 | 79s | 844 | 4376 | 0 | 0 |
| 13 | Economics | 30 | 76.67 | 87s | 914 | 5965 | 0 | 0 |
| 14 | Electronics | 30 | 46.67 | 19.6m | 8119 | 32631 | 4 | 0 |
| 15 | Energy_and_Power | 30 | 66.67 | 25.2m | 10401 | 32607 | 5 | 1 |
| 16 | Finance | 30 | 73.33 | 249s | 2610 | 13844 | 0 | 0 |
| 17 | Geography | 30 | 60.00 | 149s | 1513 | 9297 | 0 | 0 |
| 18 | History | 30 | 73.33 | 62s | 724 | 3970 | 0 | 0 |
| 19 | Literature | 30 | 83.33 | 32s | 403 | 1992 | 0 | 0 |
| 20 | Manage | 30 | 73.33 | 105s | 1135 | 6880 | 0 | 0 |
| 21 | Marketing | 30 | 93.33 | 184s | 1629 | 11119 | 0 | 0 |
| 22 | Materials | 30 | 50.00 | 27.9m | 11675 | 32591 | 6 | 0 |
| 23 | Math | 30 | 66.67 | 276s | 3066 | 14627 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 43.33 | 34.3m | 12154 | 32633 | 7 | 1 |
| 25 | Music | 30 | 36.67 | 17.6m | 6164 | 32621 | 4 | 0 |
| 26 | Pharmacy | 30 | 73.33 | 81s | 1008 | 5457 | 0 | 0 |
| 27 | Physics | 30 | 63.33 | 546s | 2808 | 32481 | 1 | 0 |
| 28 | Psychology | 30 | 73.33 | 83s | 861 | 5263 | 0 | 0 |
| 29 | Public_Health | 30 | 93.33 | 150s | 1787 | 9284 | 0 | 0 |
| 30 | Sociology | 30 | 56.67 | 510s | 1457 | 31910 | 1 | 1 |
|  | **Overall (macro avg)** | **900** | **63.22** | 236.7m |  |  | 37 | 3 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 63.22%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 63.22 |
| 차이 (Δ) | -4.18 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 863, 'length': 37}` → length(잘림) 37건 중 오답 28건
- 파싱 실패(prediction=None): 3건, 실행 오류: 0건
- completion tokens 전체: mean 3265 / median 576 / p90 8716 / p99 32578 / max 32633
- completion tokens 정답: median 466 (mean 2001) vs 오답: median 1069 (mean 5437)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 267, 'B': 220, 'C': 190, 'D': 146, 'E': 19, 'I': 2, None: 3}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 64.70 |
| open | 53 | 39.62 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 59.67 |
| Easy | 295 | 74.24 |
| Hard | 181 | 53.59 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 62.33 |
| ['Tables'] | 170 | 82.35 |
| ['Plots and Charts'] | 78 | 69.23 |
| ['Photographs'] | 75 | 58.67 |
| ['Paintings'] | 46 | 63.04 |
| ['Chemical Structures'] | 30 | 33.33 |
| ['Sheet Music'] | 30 | 36.67 |
| ['Medical Images'] | 21 | 61.90 |
| ['Microscopic Images'] | 20 | 55.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 64.71 |
| ['Technical Blueprints'] | 14 | 35.71 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Mechanical_Engineering_30 | Mechanical_Engineering | 32633 | length | False |
| validation_Electronics_11 | Electronics | 32631 | length | False |
| validation_Music_6 | Music | 32621 | length | True |
| validation_Accounting_22 | Accounting | 32611 | length | True |
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | False |
| validation_Materials_6 | Materials | 32591 | length | False |
| validation_Architecture_and_Engineering_10 | Architecture_and_Engineering | 32584 | length | True |
| validation_Electronics_5 | Electronics | 32581 | length | False |
| validation_Materials_4 | Materials | 32578 | length | False |
| validation_Accounting_20 | Accounting | 32569 | length | False |
