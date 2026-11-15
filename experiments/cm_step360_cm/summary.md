# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.06 GB |
| 총 소요 시간 | 891 s (0.25 h) 전체 / 추론 839 s / 모델 로드 52 s |
| 실행 시각 | 2026-11-13T19:51:52+09:00 → 2026-11-13T20:06:43+09:00 |
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
| 8 | Chemistry | 30 | 40.00 | 195s | 2594 | 10990 | 0 | 0 |
| 25 | Music | 30 | 30.00 | 10.7m | 2886 | 32572 | 2 | 1 |
|  | **Overall (macro avg)** | **60** | **35.00** | 14.0m |  |  | 2 | 1 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 35.00%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 35.00 |
| 차이 (Δ) | -32.40 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 58, 'length': 2}` → length(잘림) 2건 중 오답 2건
- 파싱 실패(prediction=None): 1건, 실행 오류: 0건
- completion tokens 전체: mean 2740 / median 572 / p90 6751 / p99 32572 / max 32572
- completion tokens 정답: median 527 (mean 1440) vs 오답: median 590 (mean 3440)
- prompt tokens: mean 541 / max 5653
- visual tokens/sample: mean 426 / median 156 / max 5536
- 객관식 예측 분포: `{'A': 15, 'B': 11, 'C': 8, 'D': 16, 'E': 2, None: 1}` vs 정답 분포: `{'A': 9, 'B': 24, 'C': 12, 'D': 8}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 53 | 35.85 |
| open | 7 | 28.57 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 29 | 31.03 |
| Easy | 17 | 29.41 |
| Hard | 14 | 50.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Sheet Music'] | 30 | 30.00 |
| ['Chemical Structures'] | 18 | 33.33 |
| ['Plots and Charts'] | 6 | 33.33 |
| ['Tables'] | 3 | 100.00 |
| ['Diagrams'] | 2 | 50.00 |
| ['Other'] | 1 | 0.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_9 | Music | 32572 | length | False |
| validation_Music_2 | Music | 32366 | length | False |
| validation_Chemistry_24 | Chemistry | 10990 | stop | True |
| validation_Chemistry_7 | Chemistry | 7239 | stop | False |
| validation_Music_28 | Music | 6857 | stop | False |
| validation_Chemistry_5 | Chemistry | 6751 | stop | False |
| validation_Chemistry_21 | Chemistry | 6465 | stop | False |
| validation_Chemistry_19 | Chemistry | 5817 | stop | True |
| validation_Music_1 | Music | 5811 | stop | False |
| validation_Chemistry_12 | Chemistry | 5604 | stop | False |
