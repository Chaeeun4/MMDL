# MMMU-val Baseline Evaluation Report — Qwen3-VL-4B-Instruct

- **팀명**: team4
- **팀원**: 박채은, 류다연, 이진아, 정성원
- **작성일**: 2026.09.28
- **재현 커맨드**: `bash scripts/run.sh`
  
<details>
<summary>parsor list</summary>

```
bash scripts/run.sh \
    --model_path "Qwen/Qwen3-VL-4B-Instruct"  # (필수) 평가할 모델의 HuggingFace ID 또는 로컬 경로
    --data_root "/workspace/huggingface_cache"  # (필수) 데이터셋을 저장/로드할 로컬 캐시 폴더 경로 (네트워크 볼륨)
    --output_file "results/predictions.jsonl"   # 각 문제별 모델의 예측 텍스트와 정답 여부가 기록되는 파일
    --metrics_file "results/metrics.json"       # 최종 과목별 정답률, VRAM 사용량 등 전체 통계가 저장되는 파일
    --greedy                                    # 이 플래그를 넣으면 확률이 가장 높은 단어만 고정 출력 (Temperature=0)
    --seed 3407                                 # 언제 실행해도 동일한 결과가 나오도록 고정하는 난수 시드값
    --temperature 0.7                           # 답변의 무작위성 (낮을수록 정해진 답만, 높을수록 다양한 답변)
    --top_p 0.8                                 # 누적 확률 80% 내에 속하는 단어들만 다음 단어 후보로 고려
    --top_k 20                                  # 확률이 가장 높은 상위 20개 단어만 후보로 남김
    --repetition_penalty 1.0                    # 같은 단어나 문장을 반복하는 것을 억제 (1.0이면 페널티 없음)
    --presence_penalty 1.5                      # 이전에 등장했던 단어를 다시 사용하는 것 자체에 페널티 부여
    --max_new_tokens 32768                      # 모델이 한 문제당 생성할 수 있는 최대 텍스트 길이(토큰 수)
    --min_pixels 3136                           # 모델에 입력될 이미지의 최소 픽셀 수 (이미지 깨짐 방지)
    --max_pixels 12845056                       # 모델에 입력될 이미지의 최대 픽셀 수 (VRAM 초과 에러 방지)
    --max_model_len 32768                       # 모델이 한 번에 처리하는 입력(프롬프트+이미지)+출력의 최대 총길이
    --gpu_memory_utilization 0.90               # vLLM 엔진이 24GB VRAM 중 몇 %(0.90 = 90%)를 미리 점유할지 설정
    --tensor_parallel_size 1                    # 사용할 GPU 개수 (기본값은 현재 꽂혀있는 GPU를 자동 인식)
    --max_samples 10                            # (디버깅용) 전체 데이터셋을 다 풀지 않고 처음 N문제만 풀고 종료
```

</details>
---

## 1. 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | vLLM 0.19.1 version |
| 사용 GPU | RTX 4090 (24GB vRAM) |
| 실측 peak VRAM | 22.37 GB |
| 총 소요 시간 | 699.45 sec |
| 의존성 | [requirements.txt 경로 링크](https://github.com/Chaeeun4/MMDL/blob/main/requirements.txt) |
| 실행 커맨드 | `bash run.sh `<br>`--model_path "Qwen/Qwen3-VL-4B-Instruct" `<br>`--data_root "/root/.cache/huggingface/hub/datasets--MMMU--MMMU/" `<br>`--min_pixels $((256 * 32 * 32)) `<br>`--max_pixels $((1280* 32 * 32)) `<br>`--max_new_tokens 4096 `<br>`--output_file results/opt_predictions_orig.jsonl `<br>`--metrics_file results/opt_metrics_orig.json` |

## 2. 프롬프트

**실제 모델에 들어간 프롬프트 전문** (변수 부분은 `{}`로 표시):

multiple-choice(선다형)의 경우
```
<|im_start|>user
{question}

(A) {option_A}
(B) {option_B}
(C) {option_C}
(D) {option_D}
Answer with the option's letter from the given choices directly.<|im_end|>
<|im_start|>assistant
```

open answer(서술형)의 경우
```
<|im_start|>user
{question}

Answer the question using a single word or phrase.<|im_end|>
<|im_start|>assistant
```

- **출처**: MMMU 공식 레포지토리(mmmu/configs/llava1.5.yaml) 프롬프트 템플릿 구조 및 Qwen3-VL 다중 모달 Chat Template 차용
- **선택 이유**: 최대한 공식에서 쓴 prompt 방식을 따르려고 함.

## 3. 생성(Decoding) 설정

### 3.1 Sampling recipe

| 파라미터 | 값 |
|---|---|
| `do_sample` | true |
| `temperature` | 0.7 |
| `top_p` | 0.8 |
| `top_k` | 20 |
| `repetition_penalty` | 1.0 |
| `presence_penalty` | 1.5 |
| `seed` | 3407 |

- **출처**: Qwen의 공식 instructor models Hyperparameter https://github.com/QwenLM/Qwen3-VL#instruct-models
  

### 3.2 생성 예산 / 이미지 해상도

| 파라미터 | 값 |
|---|---|
| `max_new_tokens` | 4096 |
| 이미지 해상도 처리 (`min_pixels`/`max_pixels` 등) |  `min_pixels=262144` (~0.26 MP)<br>`max_pixels=1310720` (~1.31 MP) |

**선택 근거** (본인이 사용한 인프라 제약과 어떻게 연결되는지 — 속도/VRAM/응답 잘림 등 trade-off): 900개 전체 데이터 평가 결과
- 해상도: `min_pixels=262144` (~0.26 MP), `max_pixels=1310720` (~1.31 MP) 으로 낮추어도 기본 세팅값과 정확도 차이가 없었으나(59.2% vs 59.3%), 추론 시간은 약 34%(1015초 → 673초) 단축됨
- max_new_tokens: 처음 10개 데이터로 모델 평가 시 `32768`개의 기본 토큰으로 1074 sec 가 소요됨. 전체 평가를 하려면 12-13시간 걸리기 때문에 토큰을 낮추기로 판단함. 이후 90개 데이터셋으로`max_new_tokens=32768` 인 환경에서 실험한 후 모델 answer에서 정답 토큰의 평균, 중앙값, 최대값을 분석했을 시 509, 12, 3346 이었음. max_new_tokens를 4096으로 제한하면 무한히 Perhaps로 사유하는 답변을 거르고 시간도 절약할 수 있을거라 판단. 900개 데이터에서 평가할 때도 정상 정답의 중앙값은 6-8 토큰이었으며 정답의 90%가 3200 토큰 이내에 수렴하므로, 4096 제한은 타당하다고 판단함.
  
## 4. 채점(파싱) 방식

- 사용한 파서/로직:
  MMMU 공식 레포지토리의 evaluation utils 코드를 수정함 (https://github.com/MMMU-Benchmark/MMMU/blob/main/eval/eval_utils.py)

- 동작 방식 요약:
  - 객관식: 정규표현식을 통해 (A), A. 등의 형태를 1차로 추출함.
    매칭 실패 시 모델의 출력 텍스트 전체(소문자 변환)와 객관식 보기의 원본 텍스트를 비교하는 문자열 포함 여부(Fallback)를 검사함.
    MMMU 원본 코드에 존재하던 '파싱 완전 실패 시 랜덤 알파벳 1개 찍기' 로직을 제거하고 None을 반환하도록 수정하여 평가 파이프라인의 재현성을 유지하도록 함.

  - 서술형: "answer ", "is " 등의 지시어(Indicators)를 기준으로 문장을 자른 후, 숫자 및 단위를 MMMU 정규화 규칙에 따라 정리하여 짧은 후보군 배열을 만듦. 이후 후보 텍스트가 실제 정답 문자열에 포함되는지(Containment rule) 여부로 정답을 판별함.

## 5. 결과

| No. | Subject | Data Num | Acc |
| --- | --- | --- | --- |
| 1 | Accounting | 30 | 66.67 |
| 2 | Agriculture | 30 | 60.00 |
| 3 | Architecture_and_Engineering | 30 | 36.67 |
| 4 | Art | 30 | 66.67 |
| 5 | Art_Theory | 30 | 70.00 |
| 6 | Basic_Medical_Science | 30 | 70.00 |
| 7 | Biology | 30 | 56.67 |
| 8 | Chemistry | 30 | 26.67 |
| 9 | Clinical_Medicine | 30 | 60.00 |
| 10 | Computer_Science | 30 | 60.00 |
| 11 | Design | 30 | 76.67 |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | 40.00 |
| 13 | Economics | 30 | 73.33 |
| 14 | Electronics | 30 | 40.00 |
| 15 | Energy_and_Power | 30 | 40.00 |
| 16 | Finance | 30 | 66.67 |
| 17 | Geography | 30 | 50.00 |
| 18 | History | 30 | 70.00 |
| 19 | Literature | 30 | 80.00 |
| 20 | Manage | 30 | 40.00 |
| 21 | Marketing | 30 | 86.67 |
| 22 | Materials | 30 | 46.67 |
| 23 | Math | 30 | 53.33 |
| 24 | Mechanical_Engineering | 30 | 33.33 |
| 25 | Music | 30 | 30.00 |
| 26 | Pharmacy | 30 | 73.33 |
| 27 | Physics | 30 | 63.33 |
| 28 | Psychology | 30 | 73.33 |
| 29 | Public_Health | 30 | 86.67 |
| 30 | Sociology | 30 | 60.00 |
|  | **Overall (macro avg)** | **900** | **58.56** |

계산식: `Overall = mean(30개 과목 accuracy)` 

## 6. 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | 58.56 |
| 차이 (Δ) | 8.84 |

## 7. 격차 분석

격차의 이유는 2가지 이유로 예상됨.

첫째, 평가 파이프라인의 보수성. 본 실험은 LLM Judge 없이 규칙 기반 파서를 적용해 파싱 실패 시 모두 오답 처리함. 공식 벤치마크 환경의 더 정교한 정답 추출 매칭 방식 대비 False Negative가 누적되었을 확률이 높음.

둘째, 생성 폭주 제어로 인한 정답 잘림(Truncation) 현상. 모델이 오답 생성 시 무한 루프에 빠지는 현상을 막기 위해 토큰을 4096으로 제한했으나, 이로 인해 전체 정답의 약 6~7%도 답변이 강제 종료됨. 긴 사유(Chain of Thought)가 요구되는 복잡한 문제들이 중간에 잘려 오답 처리된 구조적 손실분이 존재함.


## 8. 기타 특이사항 / 한계 (Optional)

- RTX4090 24GB VRAM을 갖춘 환경을 찾기 어려웠음
- 시간/자원 관계상 Qwen 공식 github 에서 제공한 하이퍼파라미터 (토큰, 이미지 해상도 값)으로 평가 해보지 못했음
- 실험 중 repetition_penalty 인자를 1.05로 주고 한 결과가 좋았는데 추가적인 실험을 통해서 올바른 접근인지 확안해보고 싶음
- temperature = 0.01 로 고정한 recipe로 추론을 하는 오픈소스가 있어서 현재 실험에서는 기본값보다 정확도가 높지 않기 때문에 선택하지 않았는데 더 확인하고 싶음.
- prompting 예시도 조금 더 찾아야함.
