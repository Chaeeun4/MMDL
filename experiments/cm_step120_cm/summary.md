# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.06 GB |
| 총 소요 시간 | 829 s (0.23 h) 전체 / 추론 754 s / 모델 로드 74 s |
| 실행 시각 | 2026-11-13T19:21:24+09:00 → 2026-11-13T19:35:13+09:00 |
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
| 8 | Chemistry | 30 | 43.33 | 211s | 2415 | 12354 | 0 | 0 |
| 25 | Music | 30 | 30.00 | 542s | 2390 | 32005 | 1 | 0 |
|  | **Overall (macro avg)** | **60** | **36.67** | 12.6m |  |  | 1 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 36.67%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 36.67 |
| 차이 (Δ) | -30.73 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 59, 'length': 1}` → length(잘림) 1건 중 오답 1건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 2402 / median 744 / p90 6955 / p99 32005 / max 32005
- completion tokens 정답: median 655 (mean 1892) vs 오답: median 887 (mean 2698)
- prompt tokens: mean 541 / max 5653
- visual tokens/sample: mean 426 / median 156 / max 5536
- 객관식 예측 분포: `{'A': 18, 'B': 14, 'C': 11, 'D': 9, 'E': 1}` vs 정답 분포: `{'A': 9, 'B': 24, 'C': 12, 'D': 8}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 53 | 39.62 |
| open | 7 | 14.29 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 29 | 31.03 |
| Easy | 17 | 52.94 |
| Hard | 14 | 28.57 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Sheet Music'] | 30 | 30.00 |
| ['Chemical Structures'] | 18 | 33.33 |
| ['Plots and Charts'] | 6 | 50.00 |
| ['Tables'] | 3 | 100.00 |
| ['Diagrams'] | 2 | 50.00 |
| ['Other'] | 1 | 0.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Music_27 | Music | 32005 | length | False |
| validation_Chemistry_24 | Chemistry | 12354 | stop | True |
| validation_Music_9 | Music | 8373 | stop | True |
| validation_Music_20 | Music | 8036 | stop | False |
| validation_Chemistry_7 | Chemistry | 7872 | stop | False |
| validation_Music_1 | Music | 6955 | stop | False |
| validation_Chemistry_26 | Chemistry | 5402 | stop | True |
| validation_Chemistry_21 | Chemistry | 5340 | stop | False |
| validation_Music_23 | Music | 5076 | stop | False |
| validation_Chemistry_23 | Chemistry | 5058 | stop | False |
