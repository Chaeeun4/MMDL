# MMMU-val run summary

## 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 (torch 2.10.0+cu128, transformers 5.18.0, qwen-vl-utils 0.0.14) |
| 사용 GPU | NVIDIA GeForce RTX 3090 (24 GB) (host `adsl-ubuntu`, driver 570.211.01, CUDA 12.8) |
| 실측 peak VRAM | 22.47 GB |
| 총 소요 시간 | 75 s (0.02 h) 전체 / 추론 11 s / 모델 로드 64 s |
| 실행 시각 | 2026-10-05T14:57:56+09:00 → 2026-10-05T14:59:11+09:00 |
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
| `max_new_tokens` | 4096 |
| `logprobs` | 5 |
| `min_pixels` | 65536 |
| `max_pixels` | 16777216 |
| 공식 recipe 일치 | False |

## 결과

| No. | Subject | Data Num | Acc | 소요 시간 | 평균 토큰 | 최대 토큰 | length stop | parse 실패 |
|---|---|---|---|---|---|---|---|---|
| 1 | Accounting | 30 | 40.00 | 6s | 2 | 2 | 0 | 0 |
| 4 | Art | 30 | 53.33 | 4s | 2 | 2 | 0 | 0 |
|  | **Overall (macro avg)** | **60** | **46.67** | 10s |  |  | 0 | 0 |

계산식: `Overall = mean(30개 과목 accuracy)` (= micro 46.67%, 과목당 30문제로 동일)

## 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 46.67 |
| 차이 (Δ) | -20.73 |

## 생성 진단 (격차 분석용)

- finish_reason: `{'stop': 60}` → length(잘림) 0건 중 오답 0건
- 파싱 실패(prediction=None): 0건, 실행 오류: 0건
- completion tokens 전체: mean 2 / median 2 / p90 2 / p99 2 / max 2
- completion tokens 정답: median 2 (mean 2) vs 오답: median 2 (mean 2)
- prompt tokens: mean 488 / max 1234
- visual tokens/sample: mean 396 / median 308 / max 1170
- 객관식 예측 분포: `{'A': 25, 'B': 23, 'C': 4, 'D': 8}` vs 정답 분포: `{'A': 18, 'B': 20, 'C': 14, 'D': 8}`

**문항 유형별**

| 구분 | N | Acc |
|---|---|---|
| multiple-choice | 60 | 46.67 |

**난이도별**

| 구분 | N | Acc |
|---|---|---|
| Medium | 30 | 46.67 |
| Easy | 26 | 42.31 |
| Hard | 4 | 75.00 |

**이미지 유형 (상위)별**

| 구분 | N | Acc |
|---|---|---|
| ['Tables'] | 28 | 39.29 |
| ['Paintings'] | 20 | 60.00 |
| ['Photographs'] | 5 | 20.00 |
| ['Portraits'] | 2 | 0.00 |
| ['Diagrams'] | 1 | 100.00 |
| ['Screenshots'] | 1 | 0.00 |
| ['Paintings', 'Portraits'] | 1 | 100.00 |
| ['Sculpture'] | 1 | 100.00 |
| ['Geometric Shapes'] | 1 | 100.00 |

**가장 긴 출력 Top 10**

| id | subject | tokens | finish | correct |
|---|---|---|---|---|
| validation_Accounting_1 | Accounting | 2 | stop | True |
| validation_Accounting_10 | Accounting | 2 | stop | True |
| validation_Accounting_11 | Accounting | 2 | stop | False |
| validation_Accounting_12 | Accounting | 2 | stop | True |
| validation_Accounting_13 | Accounting | 2 | stop | False |
| validation_Accounting_14 | Accounting | 2 | stop | True |
| validation_Accounting_15 | Accounting | 2 | stop | False |
| validation_Accounting_16 | Accounting | 2 | stop | False |
| validation_Accounting_17 | Accounting | 2 | stop | False |
| validation_Accounting_18 | Accounting | 2 | stop | False |
