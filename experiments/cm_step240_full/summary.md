# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.50 GB |
| 총 소요 시간 | 5859 s (1.63 h) 전체 / 추론 5755 s / 모델 로드 103 s |
| 실행 시각 | 2026-11-23T19:54:19+09:00 → 2026-11-23T21:31:58+09:00 |
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
| 1 | Accounting | 30 | 73.33 | 573s | 3131 | 32611 | 1 | 0 |
| 2 | Agriculture | 30 | 56.67 | 25s | 8 | 24 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 60.00 | 10.3m | 7714 | 17770 | 0 | 0 |
| 4 | Art | 30 | 66.67 | 4s | 5 | 13 | 0 | 0 |
| 5 | Art_Theory | 30 | 73.33 | 5s | 4 | 14 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 11s | 33 | 772 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 117s | 790 | 7294 | 0 | 0 |
| 8 | Chemistry | 30 | 36.67 | 103s | 1151 | 6686 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 66.67 | 23s | 138 | 1626 | 0 | 0 |
| 10 | Computer_Science | 30 | 56.67 | 194s | 1214 | 12835 | 0 | 0 |
| 11 | Design | 30 | 80.00 | 3s | 5 | 19 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 36.67 | 13s | 13 | 296 | 0 | 0 |
| 13 | Economics | 30 | 76.67 | 115s | 872 | 7959 | 0 | 0 |
| 14 | Electronics | 30 | 43.33 | 292s | 2797 | 15567 | 0 | 0 |
| 15 | Energy_and_Power | 30 | 66.67 | 537s | 6580 | 20572 | 0 | 0 |
| 16 | Finance | 30 | 66.67 | 559s | 2906 | 31963 | 1 | 0 |
| 17 | Geography | 30 | 50.00 | 82s | 548 | 5740 | 0 | 0 |
| 18 | History | 30 | 66.67 | 13s | 62 | 688 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 16s | 39 | 1059 | 0 | 0 |
| 20 | Manage | 30 | 46.67 | 117s | 643 | 7974 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 145s | 1170 | 9491 | 0 | 0 |
| 22 | Materials | 30 | 56.67 | 11.7m | 6860 | 32236 | 1 | 0 |
| 23 | Math | 30 | 60.00 | 212s | 2134 | 12392 | 0 | 0 |
| 24 | Mechanical_Engineering | 30 | 60.00 | 350s | 4569 | 15536 | 0 | 0 |
| 25 | Music | 30 | 30.00 | 511s | 1279 | 31878 | 1 | 0 |
| 26 | Pharmacy | 30 | 66.67 | 35s | 215 | 2542 | 0 | 0 |
| 27 | Physics | 30 | 76.67 | 149s | 1119 | 10361 | 0 | 0 |
| 28 | Psychology | 30 | 66.67 | 45s | 188 | 3098 | 0 | 0 |
| 29 | Public_Health | 30 | 90.00 | 159s | 1321 | 10212 | 0 | 0 |
| 30 | Sociology | 30 | 56.67 | 5s | 3 | 8 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **62.56** | 95.6m |  |  | 4 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 62.56%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 62.56 |
| 차이 (Δ) | -4.84 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 896, 'length': 4}` → length(잘림) 4건 중 오답 4건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 1584 / median 8 / p90 5901 / p99 17269 / max 32611
- completion tokens 정답: median 13 (mean 1195) vs 오답: median 6 (mean 2233)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 244, 'B': 195, 'C': 243, 'D': 142, 'E': 21, 'F': 2}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 65.29 |
| open | 53 | 18.87 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 59.67 |
| Easy | 295 | 71.19 |
| Hard | 181 | 55.25 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 62.33 |
| ['Tables'] | 170 | 77.06 |
| ['Plots and Charts'] | 78 | 58.97 |
| ['Photographs'] | 75 | 62.67 |
| ['Paintings'] | 46 | 60.87 |
| ['Chemical Structures'] | 30 | 36.67 |
| ['Sheet Music'] | 30 | 30.00 |
| ['Medical Images'] | 21 | 57.14 |
| ['Microscopic Images'] | 20 | 65.00 |
| ['Comics and Cartoons'] | 19 | 68.42 |
| ['Geometric Shapes'] | 17 | 64.71 |
| ['Technical Blueprints'] | 14 | 42.86 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Accounting_22 | Accounting | 32611 | length | False |
| validation_Materials_11 | Materials | 32236 | length | False |
| validation_Finance_14 | Finance | 31963 | length | False |
| validation_Music_20 | Music | 31878 | length | False |
| validation_Energy_and_Power_8 | Energy_and_Power | 20572 | stop | False |
| validation_Architecture_and_Engineering_18 | Architecture_and_Engineering | 17770 | stop | False |
| validation_Energy_and_Power_25 | Energy_and_Power | 17563 | stop | False |
| validation_Architecture_and_Engineering_27 | Architecture_and_Engineering | 17396 | stop | False |
| validation_Architecture_and_Engineering_20 | Architecture_and_Engineering | 17269 | stop | False |
| validation_Energy_and_Power_12 | Energy_and_Power | 17106 | stop | False |
