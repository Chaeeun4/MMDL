# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.29 GB |
| 총 소요 시간 | 630 s (0.17 h) 전체 / 추론 559 s / 모델 로드 70 s |
| 실행 시각 | 2026-11-15T14:13:51+09:00 → 2026-11-15T14:24:20+09:00 |
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
| 8 | Chemistry | 30 | 36.67 | 526s | 1741 | 32635 | 1 | 0 |
| 25 | Music | 30 | 33.33 | 33s | 79 | 2274 | 0 | 0 |
|  | **Overall (macro avg)** | **60** | **35.00** | 558s |  |  | 1 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 35.00%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 35.00 |
| 차이 (Δ) | -32.40 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 59, 'length': 1}` → length(잘림) 1건 중 오답 1건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 910 / median 5 / p90 2506 / p99 32635 / max 32635
- completion tokens 정답: median 6 (mean 449) vs 오답: median 5 (mean 1158)
- prompt tokens: mean 504 / max 5616
- visual tokens/sample: mean 426 / median 156 / max 5536
- 객관식 예측 분포: `{'A': 14, 'B': 10, 'C': 18, 'D': 9, 'E': 2}` vs 정답 분포: `{'A': 9, 'B': 24, 'C': 12, 'D': 8}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 53 | 39.62 |
| open | 7 | 0.00 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 29 | 34.48 |
| Easy | 17 | 29.41 |
| Hard | 14 | 42.86 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Sheet Music'] | 30 | 33.33 |
| ['Chemical Structures'] | 18 | 33.33 |
| ['Plots and Charts'] | 6 | 33.33 |
| ['Tables'] | 3 | 66.67 |
| ['Diagrams'] | 2 | 50.00 |
| ['Other'] | 1 | 0.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Chemistry_7 | Chemistry | 32635 | length | False |
| validation_Chemistry_21 | Chemistry | 4208 | stop | False |
| validation_Chemistry_5 | Chemistry | 4167 | stop | False |
| validation_Chemistry_12 | Chemistry | 3111 | stop | False |
| validation_Chemistry_24 | Chemistry | 2619 | stop | True |
| validation_Chemistry_17 | Chemistry | 2506 | stop | True |
| validation_Music_9 | Music | 2274 | stop | True |
| validation_Chemistry_15 | Chemistry | 648 | stop | True |
| validation_Chemistry_2 | Chemistry | 635 | stop | True |
| validation_Chemistry_18 | Chemistry | 527 | stop | True |
