# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.72 GB |
| 총 소요 시간 | 29782 s (8.27 h) 전체 / 추론 29679 s / 모델 로드 102 s |
| 실행 시각 | 2026-11-04T23:42:15+09:00 → 2026-11-05T07:58:37+09:00 |
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
| 1 | Accounting | 30 | 73.33 | 24.2m | 7732 | 32574 | 6 | 0 |
| 2 | Agriculture | 30 | 53.33 | 52s | 486 | 1059 | 0 | 0 |
| 3 | Architecture_and_Engineering | 30 | 40.00 | 57.0m | 20142 | 32547 | 14 | 2 |
| 4 | Art | 30 | 60.00 | 10.5m | 2568 | 32286 | 2 | 0 |
| 5 | Art_Theory | 30 | 76.67 | 513s | 1631 | 31833 | 1 | 0 |
| 6 | Basic_Medical_Science | 30 | 73.33 | 50s | 730 | 3334 | 0 | 0 |
| 7 | Biology | 30 | 53.33 | 117s | 1436 | 6895 | 0 | 0 |
| 8 | Chemistry | 30 | 40.00 | 24.5m | 8426 | 32598 | 6 | 0 |
| 9 | Clinical_Medicine | 30 | 66.67 | 17.1m | 5020 | 32594 | 4 | 0 |
| 10 | Computer_Science | 30 | 56.67 | 571s | 3471 | 32373 | 1 | 0 |
| 11 | Design | 30 | 80.00 | 27s | 550 | 1572 | 0 | 0 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 26.67 | 88s | 900 | 4984 | 0 | 0 |
| 13 | Economics | 30 | 80.00 | 521s | 2064 | 32222 | 1 | 0 |
| 14 | Electronics | 30 | 50.00 | 16.1m | 7519 | 32592 | 3 | 0 |
| 15 | Energy_and_Power | 30 | 63.33 | 53.7m | 17654 | 32565 | 14 | 0 |
| 16 | Finance | 30 | 73.33 | 10.9m | 3703 | 32472 | 2 | 1 |
| 17 | Geography | 30 | 60.00 | 540s | 2725 | 32534 | 1 | 0 |
| 18 | History | 30 | 73.33 | 506s | 1916 | 31085 | 1 | 0 |
| 19 | Literature | 30 | 80.00 | 518s | 1553 | 32562 | 1 | 1 |
| 20 | Manage | 30 | 66.67 | 10.9m | 3637 | 32364 | 2 | 0 |
| 21 | Marketing | 30 | 86.67 | 228s | 1884 | 14025 | 0 | 0 |
| 22 | Materials | 30 | 50.00 | 34.2m | 12890 | 32596 | 8 | 0 |
| 23 | Math | 30 | 66.67 | 24.5m | 8280 | 32538 | 6 | 0 |
| 24 | Mechanical_Engineering | 30 | 50.00 | 51.4m | 16324 | 32602 | 14 | 1 |
| 25 | Music | 30 | 33.33 | 47.6m | 14662 | 32608 | 13 | 0 |
| 26 | Pharmacy | 30 | 66.67 | 14.5m | 4181 | 32594 | 3 | 0 |
| 27 | Physics | 30 | 66.67 | 10.9m | 3799 | 32596 | 2 | 0 |
| 28 | Psychology | 30 | 76.67 | 68s | 882 | 4066 | 0 | 0 |
| 29 | Public_Health | 30 | 86.67 | 14.6m | 4646 | 32518 | 3 | 0 |
| 30 | Sociology | 30 | 66.67 | 511s | 1581 | 31873 | 1 | 0 |
|  | **Overall (macro avg)** | **900** | **63.22** | 494.3m |  |  | 109 | 5 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 63.22%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 63.22 |
| 차이 (Δ) | -4.18 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 791, 'length': 109}` → length(잘림) 109건 중 오답 76건
- 파싱 실패(prediction=None): 5건, 실행 오류: 0건
- completion tokens 전체: mean 5433 / median 709 / p90 32145 / p99 32594 / max 32608
- completion tokens 정답: median 614 (mean 3149) vs 오답: median 1733 (mean 9359)
- prompt tokens: mean 631 / max 5653
- visual tokens/sample: mean 488 / median 210 / max 5536
- 객관식 예측 분포: `{'A': 248, 'B': 203, 'C': 215, 'D': 155, 'E': 20, 'F': 1, None: 5}` vs 정답 분포: `{'A': 241, 'B': 230, 'C': 199, 'D': 149, 'E': 25, 'F': 2, 'I': 1}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 847 | 64.46 |
| open | 53 | 43.40 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 424 | 61.79 |
| Easy | 295 | 73.90 |
| Hard | 181 | 49.17 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Diagrams'] | 223 | 60.09 |
| ['Tables'] | 170 | 77.06 |
| ['Plots and Charts'] | 78 | 61.54 |
| ['Photographs'] | 75 | 68.00 |
| ['Paintings'] | 46 | 63.04 |
| ['Chemical Structures'] | 30 | 30.00 |
| ['Sheet Music'] | 30 | 33.33 |
| ['Medical Images'] | 21 | 66.67 |
| ['Microscopic Images'] | 20 | 65.00 |
| ['Comics and Cartoons'] | 19 | 78.95 |
| ['Geometric Shapes'] | 17 | 64.71 |
| ['Technical Blueprints'] | 14 | 57.14 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_25 | Music | 32608 | length | False |
| validation_Music_8 | Music | 32607 | length | False |
| validation_Music_28 | Music | 32604 | length | True |
| validation_Mechanical_Engineering_2 | Mechanical_Engineering | 32602 | length | False |
| validation_Chemistry_7 | Chemistry | 32598 | length | True |
| validation_Materials_1 | Materials | 32596 | length | False |
| validation_Mechanical_Engineering_30 | Mechanical_Engineering | 32596 | length | True |
| validation_Physics_29 | Physics | 32596 | length | False |
| validation_Clinical_Medicine_15 | Clinical_Medicine | 32594 | length | True |
| validation_Pharmacy_24 | Pharmacy | 32594 | length | False |
