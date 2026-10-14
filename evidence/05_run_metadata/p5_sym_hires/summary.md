# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.81 GB |
| 총 소요 시간 | 2840 s (0.79 h) 전체 / 추론 2737 s / 모델 로드 103 s |
| 실행 시각 | 2026-10-05T12:10:56+09:00 → 2026-10-05T12:58:16+09:00 |
| git | `jina` @ `47b95cee9d58bff966f4cb1f81b50f84d0c7a26c` dirty=True |

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
| `min_pixels` | 1048576 |
| `max_pixels` | 16777216 |
| 공식 recipe 일치 | True |

## 결과

| No. | Subject | Data Num | Acc | 소요 시간 | 평균 토큰 | 최대 토큰 | length stop | parse 실패 |
|---|---|---|---|---|---|---|---|---|
| 3 | Architecture_and_Engineering | 3 | 0.00 | 6s | 15 | 27 | 0 | 0 |
| 5 | Art_Theory | 4 | 100.00 | 2s | 4 | 6 | 0 | 0 |
| 6 | Basic_Medical_Science | 2 | 0.00 | 1s | 15 | 28 | 0 | 0 |
| 7 | Biology | 2 | 50.00 | 5s | 142 | 277 | 0 | 0 |
| 8 | Chemistry | 18 | 33.33 | 535s | 3281 | 31626 | 1 | 0 |
| 11 | Design | 1 | 0.00 | 0s | 4 | 4 | 0 | 0 |
| 14 | Electronics | 1 | 0.00 | 0s | 3 | 3 | 0 | 0 |
| 15 | Energy_and_Power | 3 | 66.67 | 498s | 10964 | 31576 | 1 | 1 |
| 17 | Geography | 5 | 40.00 | 497s | 6323 | 31577 | 1 | 0 |
| 18 | History | 1 | 100.00 | 0s | 7 | 7 | 0 | 0 |
| 20 | Manage | 1 | 0.00 | 5s | 408 | 408 | 0 | 0 |
| 22 | Materials | 5 | 40.00 | 145s | 3471 | 10032 | 0 | 0 |
| 23 | Math | 1 | 0.00 | 1s | 21 | 21 | 0 | 0 |
| 24 | Mechanical_Engineering | 5 | 20.00 | 498s | 6321 | 31590 | 1 | 0 |
| 25 | Music | 30 | 30.00 | 511s | 1210 | 31637 | 1 | 0 |
| 26 | Pharmacy | 11 | 63.64 | 24s | 161 | 1695 | 0 | 0 |
| 28 | Psychology | 1 | 100.00 | 0s | 2 | 2 | 0 | 0 |
| 30 | Sociology | 1 | 0.00 | 0s | 2 | 2 | 0 | 0 |
|  | **Overall (macro avg)** | **95** | **35.76** | 45.5m |  |  | 5 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 37.89%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 35.76 |
| 차이 (Δ) | -31.64 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 90, 'length': 5}` → length(잘림) 5건 중 오답 4건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 2225 / median 7 / p90 4674 / p99 31637 / max 31637
- completion tokens 정답: median 6 (mean 1524) vs 오답: median 7 (mean 2654)
- prompt tokens: mean 1557 / max 5616
- visual tokens/sample: mean 1480 / median 1065 / max 5536
- 객관식 예측 분포: `{'A': 21, 'B': 18, 'C': 35, 'D': 11, 'E': 1, None: 1}` vs 정답 분포: `{'A': 22, 'B': 29, 'C': 23, 'D': 13}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 87 | 40.23 |
| open | 8 | 12.50 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 47 | 40.43 |
| Easy | 28 | 35.71 |
| Hard | 20 | 35.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Chemical Structures'] | 30 | 36.67 |
| ['Sheet Music'] | 30 | 30.00 |
| ['Technical Blueprints'] | 14 | 28.57 |
| ['Sketches and Drafts'] | 9 | 44.44 |
| ['Diagrams', 'Technical Blueprints'] | 5 | 60.00 |
| ['Sketches and Drafts', 'Paintings'] | 2 | 100.00 |
| ['Diagrams', 'Sketches and Drafts'] | 2 | 0.00 |
| ['Photographs', 'Technical Blueprints'] | 1 | 100.00 |
| ['Sketches and Drafts', 'Medical Images'] | 1 | 100.00 |
| ['Mathematical Notations', 'Chemical Structures'] | 1 | 100.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_9 | Music | 31637 | length | False |
| validation_Chemistry_7 | Chemistry | 31626 | length | False |
| validation_Mechanical_Engineering_11 | Mechanical_Engineering | 31590 | length | False |
| validation_Geography_1 | Geography | 31577 | length | True |
| validation_Energy_and_Power_12 | Energy_and_Power | 31576 | length | False |
| validation_Materials_9 | Materials | 10032 | stop | False |
| validation_Chemistry_21 | Chemistry | 7221 | stop | True |
| validation_Chemistry_12 | Chemistry | 5342 | stop | False |
| validation_Chemistry_17 | Chemistry | 4702 | stop | True |
| validation_Chemistry_26 | Chemistry | 4674 | stop | True |
