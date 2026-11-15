# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.06 GB |
| 총 소요 시간 | 1079 s (0.30 h) 전체 / 추론 1019 s / 모델 로드 60 s |
| 실행 시각 | 2026-11-13T20:21:28+09:00 → 2026-11-13T20:39:27+09:00 |
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
| 8 | Chemistry | 30 | 56.67 | 142s | 1732 | 8697 | 0 | 0 |
| 25 | Music | 30 | 33.33 | 14.6m | 4299 | 32366 | 3 | 1 |
|  | **Overall (macro avg)** | **60** | **45.00** | 17.0m |  |  | 3 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 45.00%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 45.00 |
| 차이 (Δ) | -22.40 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 57, 'length': 3}` → length(잘림) 3건 중 오답 3건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 3015 / median 480 / p90 5056 / p99 32366 / max 32366
- completion tokens 정답: median 485 (mean 1176) vs 오답: median 475 (mean 4520)
- prompt tokens: mean 541 / max 5653
- visual tokens/sample: mean 426 / median 156 / max 5536
- 객관식 예측 분포: `{'A': 15, 'B': 13, 'C': 7, 'D': 16, 'E': 1, None: 1}` vs 정답 분포: `{'A': 9, 'B': 24, 'C': 12, 'D': 8}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 53 | 43.40 |
| open | 7 | 57.14 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 29 | 41.38 |
| Easy | 17 | 52.94 |
| Hard | 14 | 42.86 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Sheet Music'] | 30 | 33.33 |
| ['Chemical Structures'] | 18 | 50.00 |
| ['Plots and Charts'] | 6 | 50.00 |
| ['Tables'] | 3 | 100.00 |
| ['Diagrams'] | 2 | 50.00 |
| ['Other'] | 1 | 100.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_2 | Music | 32366 | length | False |
| validation_Music_1 | Music | 32201 | length | False |
| validation_Music_13 | Music | 31209 | length | False |
| validation_Music_27 | Music | 19511 | stop | False |
| validation_Chemistry_24 | Chemistry | 8697 | stop | True |
| validation_Chemistry_23 | Chemistry | 5056 | stop | False |
| validation_Music_9 | Music | 4715 | stop | True |
| validation_Chemistry_12 | Chemistry | 4301 | stop | False |
| validation_Chemistry_19 | Chemistry | 3678 | stop | True |
| validation_Music_20 | Music | 3607 | stop | False |
