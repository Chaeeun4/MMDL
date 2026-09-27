# MMMU-val Baseline Evaluation Report — Qwen3-VL-4B-Instruct

- **팀명**: team4
- **팀원**: _(기입)_
- **작성일**: 2026.09.28
- **재현 커맨드**: `(예: bash scripts/run_mmmu_eval.sh)`

---

## 1. 환경 / 재현성

| 항목 | 값 |
|---|---|
| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |
| 추론 백엔드 | _(예: transformers / vLLM, 버전)_ |
| 사용 GPU | _(모델명, VRAM)_ |
| 실측 peak VRAM | _(GB)_ |
| 총 소요 시간 | _(900문제 기준)_ |
| 의존성 | _(requirements.txt / environment.yml 경로 링크)_ |
| 실행 커맨드 | ```bash\n_(모델 checkpoint 위치와 MMMU 데이터 위치가 인자로 드러나야 함 — 예: --model_path <경로 또는 HF repo id> --data_root <MMMU 데이터 경로>. 하드코딩된 절대경로 대신 인자/환경변수로 받아서, 채점자가 자기 경로만 바꿔 끼우면 그대로 재현되게 작성)_\n``` |

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
| `max_new_tokens` | |
| 이미지 해상도 처리 (`min_pixels`/`max_pixels` 등) | |

**선택 근거** (본인이 사용한 인프라 제약과 어떻게 연결되는지 — 속도/VRAM/응답 잘림 등 trade-off): _(적절히)_

## 4. 채점(파싱) 방식

- 사용한 파서/로직: _(자체 구현 / 차용 도구명 + 링크)_
- 동작 방식 요약: _(예: 어떤 순서로 규칙을 적용하는지, 실패 시 fallback은 무엇인지)_

## 5. 결과

| No. | Subject | Data Num | Acc |
|---|---|---|---|
| 1 | Accounting | 30 | |
| 2 | Agriculture | 30 | |
| 3 | Architecture_and_Engineering | 30 | |
| 4 | Art | 30 | |
| 5 | Art_Theory | 30 | |
| 6 | Basic_Medical_Science | 30 | |
| 7 | Biology | 30 | |
| 8 | Chemistry | 30 | |
| 9 | Clinical_Medicine | 30 | |
| 10 | Computer_Science | 30 | |
| 11 | Design | 30 | |
| 12 | Diagnostics_and_Laboratory_Medicine | 30 | |
| 13 | Economics | 30 | |
| 14 | Electronics | 30 | |
| 15 | Energy_and_Power | 30 | |
| 16 | Finance | 30 | |
| 17 | Geography | 30 | |
| 18 | History | 30 | |
| 19 | Literature | 30 | |
| 20 | Manage | 30 | |
| 21 | Marketing | 30 | |
| 22 | Materials | 30 | |
| 23 | Math | 30 | |
| 24 | Mechanical_Engineering | 30 | |
| 25 | Music | 30 | |
| 26 | Pharmacy | 30 | |
| 27 | Physics | 30 | |
| 28 | Psychology | 30 | |
| 29 | Public_Health | 30 | |
| 30 | Sociology | 30 | |
| | **Overall (macro avg)** | **900** | |

계산식: `Overall = mean(30개 과목 accuracy)` _(다른 방식을 썼다면 명시)_

## 6. 공식 수치와의 비교

| | Overall (MMMU val) |
|---|---|
| 공식 (Qwen3-VL Technical Report) | 67.4 |
| 우리 재현 결과 | |
| 차이 (Δ) | |

## 7. 격차 분석

_(1000 char 이내로 작성 - Official 성능과 차이가 발생하는지, 그렇다면 그 이유를 서술. 길게 쓴다고 credit이 느는 게
아니라, 근거의 질이 핵심입니다. 레포트는 짧을수록 좋습니다.)_


## 8. 기타 특이사항 / 한계 (Optional)

_(재현 중 겪은 문제, 시간 관계상 못 해본 것, 다음에 시도해보고 싶은 것 등. 자유롭게)_
