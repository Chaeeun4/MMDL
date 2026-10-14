# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.43 GB |
| 총 소요 시간 | 6974 s (1.94 h) 전체 / 추론 6853 s / 모델 로드 121 s |
| 실행 시각 | 2026-10-05T09:55:10+09:00 → 2026-10-05T11:51:25+09:00 |
| git | `jina` @ `53eafc2f511cfad6734d32f59c6284cfc3be11cf` dirty=True |

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
| 3 | Architecture_and_Engineering | 3 | 33.33 | 14.4m | 32462 | 32504 | 3 | 0 |
| 5 | Art_Theory | 4 | 75.00 | 7s | 357 | 429 | 0 | 0 |
| 6 | Basic_Medical_Science | 2 | 0.00 | 33s | 2217 | 2417 | 0 | 0 |
| 7 | Biology | 2 | 0.00 | 8s | 474 | 534 | 0 | 0 |
| 8 | Chemistry | 18 | 44.44 | 11.1m | 6884 | 32618 | 2 | 0 |
| 11 | Design | 1 | 100.00 | 6s | 436 | 436 | 0 | 0 |
| 14 | Electronics | 1 | 0.00 | 39s | 3106 | 3106 | 0 | 0 |
| 15 | Energy_and_Power | 3 | 66.67 | 10.4m | 22356 | 32279 | 2 | 1 |
| 17 | Geography | 5 | 40.00 | 516s | 8108 | 32560 | 1 | 0 |
| 18 | History | 1 | 100.00 | 6s | 470 | 470 | 0 | 0 |
| 20 | Manage | 1 | 0.00 | 12s | 961 | 961 | 0 | 0 |
| 22 | Materials | 5 | 60.00 | 518s | 9132 | 32509 | 1 | 0 |
| 23 | Math | 1 | 100.00 | 21s | 1579 | 1579 | 0 | 0 |
| 24 | Mechanical_Engineering | 5 | 40.00 | 120s | 4735 | 8052 | 0 | 0 |
| 25 | Music | 30 | 23.33 | 47.9m | 15062 | 32633 | 13 | 0 |
| 26 | Pharmacy | 11 | 54.55 | 523s | 4777 | 32617 | 1 | 0 |
| 28 | Psychology | 1 | 100.00 | 8s | 614 | 614 | 0 | 0 |
| 30 | Sociology | 1 | 0.00 | 7s | 489 | 489 | 0 | 0 |
|  | **Overall (macro avg)** | **95** | **46.52** | 114.1m |  |  | 23 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 40.00%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 46.52 |
| 차이 (Δ) | -20.88 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'length': 23, 'stop': 72}` → length(잘림) 23건 중 오답 20건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 9654 / median 2417 / p90 32509 / p99 32633 / max 32633
- completion tokens 정답: median 1463 (mean 4445) vs 오답: median 4906 (mean 13127)
- prompt tokens: mean 505 / max 5627
- visual tokens/sample: mean 417 / median 144 / max 5536
- 객관식 예측 분포: `{'A': 27, 'B': 18, 'C': 22, 'D': 19, None: 1}` vs 정답 분포: `{'A': 22, 'B': 29, 'C': 23, 'D': 13}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 87 | 42.53 |
| open | 8 | 12.50 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 47 | 46.81 |
| Easy | 28 | 39.29 |
| Hard | 20 | 25.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Chemical Structures'] | 30 | 43.33 |
| ['Sheet Music'] | 30 | 23.33 |
| ['Technical Blueprints'] | 14 | 35.71 |
| ['Sketches and Drafts'] | 9 | 77.78 |
| ['Diagrams', 'Technical Blueprints'] | 5 | 40.00 |
| ['Sketches and Drafts', 'Paintings'] | 2 | 100.00 |
| ['Diagrams', 'Sketches and Drafts'] | 2 | 0.00 |
| ['Photographs', 'Technical Blueprints'] | 1 | 100.00 |
| ['Sketches and Drafts', 'Medical Images'] | 1 | 0.00 |
| ['Mathematical Notations', 'Chemical Structures'] | 1 | 100.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_8 | Music | 32633 | length | False |
| validation_Chemistry_14 | Chemistry | 32618 | length | False |
| validation_Pharmacy_17 | Pharmacy | 32617 | length | False |
| validation_Music_22 | Music | 32614 | length | False |
| validation_Music_6 | Music | 32610 | length | False |
| validation_Geography_1 | Geography | 32560 | length | False |
| validation_Music_19 | Music | 32552 | length | False |
| validation_Music_14 | Music | 32521 | length | False |
| validation_Chemistry_19 | Chemistry | 32514 | length | True |
| validation_Materials_9 | Materials | 32509 | length | False |
