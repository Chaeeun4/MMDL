# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.60 GB |
| 총 소요 시간 | 6998 s (1.94 h) 전체 / 추론 6894 s / 모델 로드 104 s |
| 실행 시각 | 2026-10-05T12:58:25+09:00 → 2026-10-05T14:55:03+09:00 |
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
| `min_pixels` | 65536 |
| `max_pixels` | 16777216 |
| 공식 recipe 일치 | True |

## 결과

| No. | Subject | Data Num | Acc | 소요 시간 | 평균 토큰 | 최대 토큰 | length stop | parse 실패 |
|---|---|---|---|---|---|---|---|---|
| 3 | Architecture_and_Engineering | 3 | 66.67 | 10.9m | 25619 | 32474 | 2 | 0 |
| 5 | Art_Theory | 4 | 100.00 | 9s | 473 | 608 | 0 | 0 |
| 6 | Basic_Medical_Science | 2 | 0.00 | 29s | 2103 | 2114 | 0 | 0 |
| 7 | Biology | 2 | 0.00 | 28s | 1280 | 2122 | 0 | 0 |
| 8 | Chemistry | 18 | 22.22 | 17.5m | 9730 | 32598 | 4 | 1 |
| 11 | Design | 1 | 100.00 | 3s | 239 | 239 | 0 | 0 |
| 14 | Electronics | 1 | 0.00 | 70s | 5442 | 5442 | 0 | 0 |
| 15 | Energy_and_Power | 3 | 66.67 | 10.4m | 22028 | 32253 | 2 | 0 |
| 17 | Geography | 5 | 40.00 | 134s | 4005 | 9159 | 0 | 0 |
| 18 | History | 1 | 100.00 | 8s | 621 | 621 | 0 | 0 |
| 20 | Manage | 1 | 100.00 | 13s | 1073 | 1073 | 0 | 0 |
| 22 | Materials | 5 | 80.00 | 118s | 4915 | 7733 | 0 | 0 |
| 23 | Math | 1 | 100.00 | 8s | 562 | 562 | 0 | 0 |
| 24 | Mechanical_Engineering | 5 | 20.00 | 10.5m | 13729 | 32581 | 2 | 0 |
| 25 | Music | 30 | 40.00 | 47.6m | 14663 | 32609 | 13 | 0 |
| 26 | Pharmacy | 11 | 63.64 | 10.6m | 7474 | 32594 | 2 | 0 |
| 28 | Psychology | 1 | 100.00 | 11s | 865 | 865 | 0 | 0 |
| 30 | Sociology | 1 | 0.00 | 7s | 548 | 548 | 0 | 0 |
|  | **Overall (macro avg)** | **95** | **55.51** | 114.8m |  |  | 25 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 45.26%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 55.51 |
| 차이 (Δ) | -11.89 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'length': 25, 'stop': 70}` → length(잘림) 25건 중 오답 13건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 10226 / median 2758 / p90 32580 / p99 32609 / max 32609
- completion tokens 정답: median 1266 (mean 10161) vs 오답: median 3107 (mean 10279)
- prompt tokens: mean 531 / max 5653
- visual tokens/sample: mean 417 / median 144 / max 5536
- 객관식 예측 분포: `{'A': 30, 'B': 22, 'C': 18, 'D': 16, None: 1}` vs 정답 분포: `{'A': 22, 'B': 29, 'C': 23, 'D': 13}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 87 | 48.28 |
| open | 8 | 12.50 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 47 | 40.43 |
| Easy | 28 | 64.29 |
| Hard | 20 | 30.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Chemical Structures'] | 30 | 33.33 |
| ['Sheet Music'] | 30 | 40.00 |
| ['Technical Blueprints'] | 14 | 57.14 |
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
| validation_Music_3 | Music | 32609 | length | False |
| validation_Music_25 | Music | 32608 | length | False |
| validation_Music_8 | Music | 32607 | length | False |
| validation_Music_28 | Music | 32604 | length | True |
| validation_Chemistry_7 | Chemistry | 32598 | length | True |
| validation_Pharmacy_24 | Pharmacy | 32594 | length | True |
| validation_Music_22 | Music | 32588 | length | True |
| validation_Music_6 | Music | 32584 | length | True |
| validation_Mechanical_Engineering_12 | Mechanical_Engineering | 32581 | length | False |
| validation_Chemistry_5 | Chemistry | 32580 | length | False |
