# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.79 GB |
| 총 소요 시간 | 9968 s (2.77 h) 전체 / 추론 9836 s / 모델 로드 132 s |
| 실행 시각 | 2026-11-23T23:08:39+09:00 → 2026-11-24T01:54:48+09:00 |
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
| 1 | Accounting | 30 | 70.00 | 15.1m | 5333 | 32611 | 3 | 0 |
| 2 | Agriculture | 30 | 56.67 | 26s | 9 | 24 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 60.00 | 24.3m | 10945 | 32526 | 4 | 1 |
| 4 | Art | 30 | 63.33 | 5s | 6 | 13 | 0 | 0 |
| 5 | Art_Theory | 30 | 73.33 | 5s | 6 | 14 | 0 | 0 |
| 6 | Basic_Medical_Science | 30 | 70.00 | 2s | 8 | 28 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 66s | 540 | 4175 | 0 | 0 |
| 8 | Chemistry | 30 | 33.33 | 155s | 1312 | 9991 | 0 | 0 |
| 9 | Clinical_Medicine | 30 | 70.00 | 5s | 14 | 199 | 0 | 0 |
| 10 | Computer_Science | 30 | 53.33 | 129s | 887 | 8630 | 0 | 0 |
| 11 | Design | 30 | 80.00 | 3s | 7 | 21 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 36.67 | 10s | 6 | 20 | 0 | 0 |
| 13 | Economics | 30 | 70.00 | 96s | 781 | 6667 | 0 | 0 |
| 14 | Electronics | 30 | 50.00 | 561s | 2897 | 32548 | 1 | 0 |
| 15 | Energy_and_Power | 30 | 56.67 | 27.8m | 11250 | 32607 | 6 | 2 |
| 16 | Finance | 30 | 66.67 | 173s | 1775 | 10208 | 0 | 0 |
| 17 | Geography | 30 | 60.00 | 160s | 1151 | 10069 | 0 | 0 |
| 18 | History | 30 | 70.00 | 4s | 13 | 29 | 0 | 0 |
| 19 | Literature | 30 | 80.00 | 4s | 5 | 15 | 0 | 0 |
| 20 | Manage | 30 | 43.33 | 122s | 628 | 8463 | 0 | 0 |
| 21 | Marketing | 30 | 86.67 | 102s | 805 | 6961 | 0 | 0 |
| 22 | Materials | 30 | 46.67 | 23.5m | 9320 | 32520 | 5 | 0 |
| 23 | Math | 30 | 73.33 | 559s | 2970 | 32006 | 1 | 0 |
| 24 | Mechanical_Engineering | 30 | 50.00 | 21.6m | 7838 | 32552 | 5 | 0 |
| 25 | Music | 30 | 30.00 | 10.6m | 2401 | 32238 | 2 | 0 |
| 26 | Pharmacy | 30 | 70.00 | 36s | 167 | 2685 | 0 | 0 |
| 27 | Physics | 30 | 70.00 | 95s | 812 | 6761 | 0 | 0 |
| 28 | Psychology | 30 | 76.67 | 8s | 46 | 299 | 0 | 0 |
| 29 | Public_Health | 30 | 90.00 | 120s | 1073 | 7851 | 0 | 0 |
| 30 | Sociology | 30 | 63.33 | 5s | 6 | 25 | 0 | 0 |
|  | **Overall (macro avg)** | **900** | **62.44** | 163.6m |  |  | 27 | 3 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 62.44%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 62.44 |
| 차이 (Δ) | -4.96 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 873, 'length': 27}` → length(잘림) 27건 중 오답 18건
- 파싱 실패(prediction=None): 3건, 실행 오류: 0건
- completion tokens 전체: mean 2100 / median 9 / p90 6301 / p99 32526 / max 32611
- completion tokens 정답: median 13 (mean 1537) vs 오답: median 8 (mean 3038)
- prompt tokens: mean 594 / max 5616
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 243, 'B': 196, 'C': 237, 'D': 146, 'E': 20, 'F': 2, None: 3}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 65.64 |
| open | 53 | 11.32 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 61.79 |
| Easy | 295 | 70.17 |
| Hard | 181 | 51.38 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 62.33 |
| ['Tables'] | 170 | 75.88 |
| ['Plots and Charts'] | 78 | 58.97 |
| ['Photographs'] | 75 | 64.00 |
| ['Paintings'] | 46 | 65.22 |
| ['Chemical Structures'] | 30 | 30.00 |
| ['Sheet Music'] | 30 | 30.00 |
| ['Medical Images'] | 21 | 66.67 |
| ['Microscopic Images'] | 20 | 60.00 |
| ['Comics and Cartoons'] | 19 | 73.68 |
| ['Geometric Shapes'] | 17 | 70.59 |
| ['Technical Blueprints'] | 14 | 35.71 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Accounting_22 | Accounting | 32611 | length | True |
| validation_Energy_and_Power_14 | Energy_and_Power | 32607 | length | True |
| validation_Energy_and_Power_8 | Energy_and_Power | 32602 | length | True |
| validation_Energy_and_Power_9 | Energy_and_Power | 32570 | length | True |
| validation_Accounting_20 | Accounting | 32569 | length | False |
| validation_Mechanical_Engineering_23 | Mechanical_Engineering | 32552 | length | True |
| validation_Electronics_22 | Electronics | 32548 | length | False |
| validation_Architecture_and_Engineering_9 | Architecture_and_Engineering | 32526 | length | False |
| validation_Energy_and_Power_1 | Energy_and_Power | 32526 | length | False |
| validation_Materials_9 | Materials | 32520 | length | False |
