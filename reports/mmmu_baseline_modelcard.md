# MMMU-val Baseline Evaluation Report — Qwen3-VL-4B-Instruct (model-card / official recipe run)

- **팀명**: team4
- **팀원**: 박채은, 류다연, 이진아, 정성원
- **작성자(이 run)**: 이진아 (branch `jina`)
- **작성일**: _(run 완료 후 기입)_
- **재현 커맨드**: `bash scripts/run_baseline_modelcard.sh --gpu 0 --run_name baseline_modelcard_v1`

> 이 리포트는 `SUBMISSION_TEMPLATE.md` 구조를 따르며, 이전 제출본(`reports/mmmu_baseline.md`, 4096 토큰·축소 해상도)과
> **동일한 프롬프트·파서**를 쓰되 생성 설정만 **Qwen 모델 카드/공식 README의 Instruct recipe 전체 값**으로 되돌린 run입니다.
> `TBD` 로 표시된 값은 run 종료 후 `runs/baseline_modelcard_v1/summary.md` 의 값으로 교체합니다.

```
bash scripts/run_baseline_modelcard.sh \
    --gpu 0                       # 사용할 GPU index (CUDA_VISIBLE_DEVICES)
    --run_name baseline_modelcard_v1   # 산출물 폴더 runs/<run_name>/
    [--resume] [--smoke] [--fg]   # 재개 / 2과목 빠른 점검 / 포그라운드
# 내부적으로 실행되는 커맨드 (runs/<run_name>/command.txt 에 그대로 기록됨):
python code/run_mmmu.py \
    --model_path Qwen/Qwen3-VL-4B-Instruct   # (필수) HF id 또는 로컬 경로. revision은 코드에 pin
    --data_root $HF_HOME                     # (필수) MMMU 가 캐시되는 HF 캐시 경로
    --run_dir runs/baseline_modelcard_v1     # 모든 산출물 위치
    --batch_mode subject                     # 과목별 generate → 과목별 소요시간 + 체크포인트/재개
    --logprobs 5                             # 토큰 logprob 요약 저장 (첫 토큰 top-5, 평균/최저)
    --seed 3407 --temperature 0.7 --top_p 0.8 --top_k 20 \
    --repetition_penalty 1.0 --presence_penalty 1.5 --max_new_tokens 32768   # 공식 Instruct recipe
    --min_pixels auto --max_pixels auto      # 체크포인트 processor 기본값 사용 (실제 값은 manifest.json 에 기록)
    --max_model_len 32768 --gpu_memory_utilization 0.90
```

## 1. 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17), bf16, 양자화 없음 |
| 추론 백엔드 | vLLM (버전은 `runs/<run>/manifest.json → environment.packages.vllm`; lock 파일 기준 0.19.1). 선택 이유: Qwen 공식 평가 런타임이 vLLM이고, 900문제 × 최대 32k 토큰 생성을 단일 24GB GPU에서 현실적인 시간에 끝내려면 continuous batching이 필요함 |
| 사용 GPU | TBD (`manifest.json → environment.gpus`) |
| 실측 peak VRAM | TBD GB (`metrics.json → peak_vram_gb`, nvidia-smi 0.5초 폴링 최대값; `gpu_monitor.csv` 시계열도 보관) |
| 총 소요 시간 | TBD s (`metrics.json → elapsed_seconds`; 과목별 시간은 `subject_timing`) |
| 의존성 | [requirements.txt](../requirements.txt) / [requirements-lock.txt](../requirements-lock.txt) (실제 설치본은 `runs/<run>/pip_freeze.txt`) |
| 실행 커맨드 | `bash scripts/run_baseline_modelcard.sh --gpu <N> --run_name <name>` (`MODEL_PATH`, `DATA_ROOT`, `HF_HOME` 환경변수로 경로 교체 가능) |

## 2. 프롬프트

**실제 모델에 들어간 프롬프트 전문** (변수 부분은 `{}`로 표시; Qwen3-VL chat template 적용 후 문자열. 실제 예시는 `manifest.json → prompt_example`):

multiple-choice(선다형)
```
<|im_start|>user
{question (본문 중 <image N> 자리에 <|vision_start|><|image_pad|>...<|vision_end|> 가 삽입됨)}

(A) {option_A}
(B) {option_B}
(C) {option_C}
(D) {option_D}
Answer with the option's letter from the given choices directly.<|im_end|>
<|im_start|>assistant
```

open answer(서술형)
```
<|im_start|>user
{question}

Answer the question using a single word or phrase.<|im_end|>
<|im_start|>assistant
```

- **출처**: MMMU 공식 레포지토리 `mmmu/configs/llava1.5.yaml` 의 `multi_choice_example_format` / `short_ans_example_format` 템플릿 + Qwen3-VL 공식 chat template (`processor.apply_chat_template`). 구현: [`code/prompt.py`](../code/prompt.py)
- **선택 이유**: MMMU 공식 프롬프트를 그대로 써서 공식 수치와 비교 가능하게 하고, 이전 제출본과 동일하게 유지하여 생성 설정 변경 효과만 분리해서 보기 위함. 시스템 프롬프트는 넣지 않음(Qwen3-VL 기본 템플릿도 시스템 프롬프트 없음).

## 3. 생성(Decoding) 설정

### 3.1 Sampling recipe

| 파라미터 | 값 |
|---|---|
| `do_sample` | true (`greedy='false'`) |
| `temperature` | 0.7 |
| `top_p` | 0.8 |
| `top_k` | 20 |
| `repetition_penalty` | 1.0 |
| `presence_penalty` | 1.5 |
| `seed` | 3407 |
| `max_new_tokens` (`out_seq_length`) | 32768 |

- **출처**: Qwen3-VL 공식 GitHub README → "Evaluation Reproduction → Generation Hyperparameters → Instruct models" (https://github.com/QwenLM/Qwen3-VL#evaluation-reproduction). 위 8개 값을 **하나도 바꾸지 않고** 사용 (manifest의 `sampling.matches_official_instruct_recipe == true` 로 자동 검증). vLLM `SamplingParams` 에 그대로 매핑되며 `stop_token_ids=[151645, 151643]` (`<|im_end|>`, `<|endoftext|>`)만 명시.

### 3.2 생성 예산 / 이미지 해상도

| 파라미터 | 값 |
|---|---|
| `max_new_tokens` | 32768 (공식 `out_seq_length`) |
| 이미지 해상도 처리 (`min_pixels`/`max_pixels`) | 체크포인트의 `preprocessor_config.json` 기본값 (`image_processor.size.shortest_edge` / `longest_edge`) 을 실행 시 읽어 그대로 사용. 실제 적용값: TBD (`manifest.json → resolved.min_pixels/max_pixels`, 출처 필드 포함) |
| `max_model_len` | 32768 |

**선택 근거**: 이번 run의 목적은 "모델 카드가 말하는 그대로"의 baseline을 확보하는 것이므로 생성 예산과 해상도 모두 공식/기본값을 그대로 둠. 비용: 이전 제출본에서 `max_new_tokens=4096` 으로 자른 이유였던 장문 추론 루프(이전 run에서 900문제 중 **124문제가 4096 토큰에서 잘렸고 그중 92문제가 오답**)를 이번에는 32768까지 허용하므로 추론 시간이 약 10배(RTX 4090 기준 7~11시간 예상) 늘어남. 이를 감당하기 위해 (1) 과목별 체크포인트/재개, (2) 백그라운드 실행(`setsid nohup`), (3) GPU 시계열 로깅을 붙임. 해상도는 축소하지 않으므로 큰 이미지 문항의 prompt 토큰이 늘어나지만 MMMU 이미지 대부분은 1 MP 이하라 32768 컨텍스트 안에 들어옴(초과 시 해당 문항만 개별 재시도 후 error 로 기록).

## 4. 채점(파싱) 방식

- 사용한 파서/로직: MMMU 공식 `eval/eval_utils.py` 를 변형한 자체 구현 [`code/parser.py`](../code/parser.py), [`code/evaluator.py`](../code/evaluator.py) (이전 제출본과 동일, 변경 없음)
- 동작 방식 요약:
  - 객관식: ① 마지막 `Answer:` 뒤에서 유일한 선지 문자 탐색 → ② `(A)` 형태 → ③ ` A ` 독립 토큰 → ④ `A.` → ⑤ 응답이 5단어 초과면 선지 본문 문자열 포함 여부. 복수 후보면 **마지막 등장** 선택. 모두 실패 시 공식 코드의 랜덤 선택 대신 `None` 반환(오답 처리) → 재현성 확보.
  - 서술형: 공식 `parse_open_response` 와 동일하게 "answer ", "is ", "=" 등 지시어 뒤 짧은 구간을 후보로 뽑고 숫자 추출·정규화(소수 2자리 반올림, 소문자, 1글자 패딩) 후 gold 문자열 포함 여부(containment)로 채점.
  - LLM judge 미사용. 종합 점수 = 30개 과목 정확도 단순 평균(macro).

## 5. 결과

_(run 완료 후 `runs/baseline_modelcard_v1/summary.md` 의 표를 그대로 붙여넣기. 소요 시간/토큰/잘림/파싱 실패 열 포함)_

| No. | Subject | Data Num | Acc | 과목 소요 시간 |
| --- | --- | --- | --- | --- |
| 1 | Accounting | 30 | TBD | TBD |
| 2 | Agriculture | 30 | TBD | TBD |
| 3 | Architecture_and_Engineering | 30 | TBD | TBD |
| 4 | Art | 30 | TBD | TBD |
| 5 | Art_Theory | 30 | TBD | TBD |
| 6 | Basic_Medical_Science | 30 | TBD | TBD |
| 7 | Biology | 30 | TBD | TBD |
| 8 | Chemistry | 30 | TBD | TBD |
| 9 | Clinical_Medicine | 30 | TBD | TBD |
| 10 | Computer_Science | 30 | TBD | TBD |
| 11 | Design | 30 | TBD | TBD |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | TBD | TBD |
| 13 | Economics | 30 | TBD | TBD |
| 14 | Electronics | 30 | TBD | TBD |
| 15 | Energy_and_Power | 30 | TBD | TBD |
| 16 | Finance | 30 | TBD | TBD |
| 17 | Geography | 30 | TBD | TBD |
| 18 | History | 30 | TBD | TBD |
| 19 | Literature | 30 | TBD | TBD |
| 20 | Manage | 30 | TBD | TBD |
| 21 | Marketing | 30 | TBD | TBD |
| 22 | Materials | 30 | TBD | TBD |
| 23 | Math | 30 | TBD | TBD |
| 24 | Mechanical_Engineering | 30 | TBD | TBD |
| 25 | Music | 30 | TBD | TBD |
| 26 | Pharmacy | 30 | TBD | TBD |
| 27 | Physics | 30 | TBD | TBD |
| 28 | Psychology | 30 | TBD | TBD |
| 29 | Public_Health | 30 | TBD | TBD |
| 30 | Sociology | 30 | TBD | TBD |
|  | **Overall (macro avg)** | **900** | **TBD** | TBD |

계산식: `Overall = mean(30개 과목 accuracy)` (과목당 30문제이므로 900문제 micro 정확도와 동일; `summary.md` 에 둘 다 출력됨)

## 6. 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 (model-card 설정) | TBD |
| 차이 (Δ) | TBD |
| (참고) 이전 제출본 (4096 토큰, 256–1280 visual tokens) | 58.56 |

## 7. 격차 분석

_(run 완료 후 1000자 이내로 작성. 아래는 이전 run 데이터로 세워 둔 가설과, 이번 run에서 바로 확인할 수 있는 근거 항목)_

- **가설 1 — 출력 잘림**: 이전 run은 124/900 문항이 4096 토큰에서 잘렸고(그중 오답 92), 특히 Energy_and_Power(20건), Materials(18), Architecture(17), Mechanical(14) 등 계산형 과목에 집중됨. 공식 32768 예산에서 `finish_reason=length` 가 얼마나 줄고 해당 과목 정확도가 얼마나 회복되는지 → `summary.md` 의 "length stop" 열과 `summary_vs_orig.md` 의 W→C 전이로 확인.
- **가설 2 — 파서 보수성**: 랜덤 fallback 제거 + LLM judge 미사용으로 `prediction=None` 14건은 전부 오답. 서술형(open) 53문항 정확도 20.8% vs 객관식 60.9% → 공식 평가(VLMEvalKit/lmms-eval 의 judge 기반 추출)와의 구조적 차이. 이번 run의 `prediction_none` 과 `by_question_type` 으로 재확인.
- **가설 3 — 해상도**: 이전 run은 visual token 상한 1280. 이번 run의 `images[*].visual_tokens` 와 `img_type` 별 정확도(Technical Blueprints 28.6%, Chemical Structures 30%, Sheet Music 30% 이 낮았음)를 비교.
- **가설 4 — 샘플링 분산**: 동일 recipe라도 sampling 이므로 seed 고정 하에서도 vLLM 배치 구성이 바뀌면 결과가 달라질 수 있음. 과목별 배치가 이전 run(전체 배치)과 다르므로 ±1~2p 변동은 노이즈 범위로 간주.

## 8. 기타 특이사항 / 한계

- 이 run은 재현성/비교 기준점 확보가 목적이며, 모든 문항에 대해 프롬프트 전문·raw 출력·토큰 수·logprob 요약·이미지 크기·타이밍·MMMU 정답 해설을 `predictions.jsonl` 에 남겨 이후 fine-tuning 데이터 설계와 오답 분석에 그대로 쓸 수 있게 함 (`docs/baseline_modelcard_runbook.md` 5절 참고).
- 공식 README는 "일부 벤치마크는 프롬프트를 약간 수정했다"고만 밝히고 세부는 technical report 로 미룸 → 공식 프롬프트와의 잔여 차이는 제거 불가.
- 이번 run 의 모든 산출물은 `runs/baseline_modelcard_v1/` 에 보관.
