# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.29 GB |
| 총 소요 시간 | 169 s (0.05 h) 전체 / 추론 105 s / 모델 로드 63 s |
| 실행 시각 | 2026-11-15T14:29:09+09:00 → 2026-11-15T14:31:57+09:00 |
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
| 8 | Chemistry | 30 | 33.33 | 86s | 656 | 5538 | 0 | 0 |
| 25 | Music | 30 | 30.00 | 19s | 42 | 1154 | 0 | 0 |
|  | **Overall (macro avg)** | **60** | **31.67** | 104s |  |  | 0 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 31.67%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 31.67 |
| 차이 (Δ) | -35.73 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 60}` → length(잘림) 0건 중 오답 0건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 349 / median 5 / p90 1154 / p99 5538 / max 5538
- completion tokens 정답: median 5 (mean 344) vs 오답: median 5 (mean 351)
- prompt tokens: mean 504 / max 5616
- visual tokens/sample: mean 426 / median 156 / max 5536
- 객관식 예측 분포: `{'A': 10, 'B': 11, 'C': 20, 'D': 11, 'E': 1}` vs 정답 분포: `{'A': 9, 'B': 24, 'C': 12, 'D': 8}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 53 | 35.85 |
| open | 7 | 0.00 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 29 | 27.59 |
| Easy | 17 | 29.41 |
| Hard | 14 | 42.86 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Sheet Music'] | 30 | 30.00 |
| ['Chemical Structures'] | 18 | 27.78 |
| ['Plots and Charts'] | 6 | 33.33 |
| ['Tables'] | 3 | 66.67 |
| ['Diagrams'] | 2 | 50.00 |
| ['Other'] | 1 | 0.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Chemistry_7 | Chemistry | 5538 | stop | False |
| validation_Chemistry_21 | Chemistry | 4466 | stop | False |
| validation_Chemistry_24 | Chemistry | 3941 | stop | True |
| validation_Chemistry_12 | Chemistry | 3045 | stop | False |
| validation_Chemistry_17 | Chemistry | 1379 | stop | True |
| validation_Music_9 | Music | 1154 | stop | False |
| validation_Chemistry_2 | Chemistry | 650 | stop | True |
| validation_Chemistry_15 | Chemistry | 493 | stop | True |
| validation_Chemistry_28 | Chemistry | 21 | stop | False |
| validation_Chemistry_18 | Chemistry | 19 | stop | True |
