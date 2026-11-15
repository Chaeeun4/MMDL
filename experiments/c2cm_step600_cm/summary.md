# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.29 GB |
| 총 소요 시간 | 723 s (0.20 h) 전체 / 추론 663 s / 모델 로드 60 s |
| 실행 시각 | 2026-11-15T14:32:49+09:00 → 2026-11-15T14:44:52+09:00 |
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
| 8 | Chemistry | 30 | 33.33 | 149s | 1062 | 9630 | 0 | 0 |
| 25 | Music | 30 | 33.33 | 513s | 1090 | 32609 | 1 | 0 |
|  | **Overall (macro avg)** | **60** | **33.33** | 11.0m |  |  | 1 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 33.33%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 33.33 |
| 차이 (Δ) | -34.07 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 59, 'length': 1}` → length(잘림) 1건 중 오답 0건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 1076 / median 5 / p90 2370 / p99 32609 / max 32609
- completion tokens 정답: median 7 (mean 2508) vs 오답: median 5 (mean 360)
- prompt tokens: mean 504 / max 5616
- visual tokens/sample: mean 426 / median 156 / max 5536
- 객관식 예측 분포: `{'A': 12, 'B': 11, 'C': 20, 'D': 9, 'E': 1}` vs 정답 분포: `{'A': 9, 'B': 24, 'C': 12, 'D': 8}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 53 | 37.74 |
| open | 7 | 0.00 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 29 | 27.59 |
| Easy | 17 | 29.41 |
| Hard | 14 | 50.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Sheet Music'] | 30 | 33.33 |
| ['Chemical Structures'] | 18 | 27.78 |
| ['Plots and Charts'] | 6 | 33.33 |
| ['Tables'] | 3 | 66.67 |
| ['Diagrams'] | 2 | 50.00 |
| ['Other'] | 1 | 0.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_9 | Music | 32609 | length | True |
| validation_Chemistry_24 | Chemistry | 9630 | stop | True |
| validation_Chemistry_7 | Chemistry | 5919 | stop | False |
| validation_Chemistry_21 | Chemistry | 5361 | stop | True |
| validation_Chemistry_12 | Chemistry | 3093 | stop | False |
| validation_Chemistry_5 | Chemistry | 2370 | stop | False |
| validation_Chemistry_17 | Chemistry | 1827 | stop | False |
| validation_Chemistry_2 | Chemistry | 1128 | stop | True |
| validation_Chemistry_18 | Chemistry | 662 | stop | True |
| validation_Chemistry_14 | Chemistry | 588 | stop | False |
