# Qwen3-VL-4B-Instruct × MMMU 실험 정리

작성: 이진아 (branch `jina`) · 환경: RTX 3090 24GB 1장, vLLM 0.19.1, 서버 `/data/jinagg`

모델 `Qwen/Qwen3-VL-4B-Instruct` (rev `ebb281ec`) 를 MMMU validation 900문항으로 평가하고,
"왜 공식 수치(67.4)보다 낮은가 / 어디가 약한가"를 분리해서 보기 위한 실험들입니다.
모든 수치는 `experiments/<run>/` 의 `metrics.json`, `predictions.jsonl.gz` 에서 재계산할 수 있습니다.

## 1. 한눈에 보기

| 구분 | 결과 |
|---|---|
| 공식 recipe baseline (`baseline_modelcard_v1`) | **61.1%** (550/900), 객관식 63.9%, 서술형 17.0% — 공식 67.4 대비 -6.3%p |
| 이전 제출본 (4096 토큰 / 축소 해상도) | 58.6% |
| seed만 바꾼 재실행 (노이즈 기준선) | 60.1% — 900문항 중 59문항(6.6%)이 정오 뒤바뀜 |
| 가장 약한 이미지 유형 | Sketches 28.6, Chemical Structures 29.0, Sheet Music 33.3, Blueprints 40.0 (4개 합 n=95, 32.6%) |
| 가장 큰 개선 | 서술형에 "단계별 풀이 + Answer:" 프롬프트: 17.0 → 39.6% (+22.6%p, McNemar p=0.0075) |

### 판정 규칙
`W→C − C→W` 가 seed 노이즈의 net 변화보다 확실히 크고 McNemar p < 0.05 일 때만 "개선"으로 적습니다.
seed만 바꿔도 6.6%의 문항이 뒤집히므로, 그 이하의 차이는 노이즈입니다.

## 2. 같은 문항 비교표 (baseline 대비)

| run | 설정 | n | baseline | run | Δ(%p) | W→C / C→W | McNemar p | 평균 토큰 | 길이 초과 |
|---|---|---|---|---|---|---|---|---|---|
| p1_noise_seed1234 | seed=1234 | 900 | 61.1 | 60.1 | -1.0 | 25 / 34 | 0.298 | 2871 | 54 |
| abl_temp0 | temperature=0 | 900 | 61.1 | 58.6 | -2.6 | 21 / 44 | 0.0059 | 3819 | 94 |
| abl_cot_open | 서술형 53문항, CoT 프롬프트 | 53 | 17.0 | 39.6 | **+22.6** | 15 / 3 | 0.0075 | 4884 | 4 |
| p3_sym_cot | 기호·도식 95문항, 단계별 풀이 | 95 | 32.6 | 40.0 | +7.4 | 16 / 9 | 0.23 | 9654 | 23 |
| p4_sym_textonly | 같은 95문항, 이미지 제거 | 95 | 32.6 | 24.2 | -8.4 | 7 / 15 | 0.134 | 822 | 2 |
| p5_sym_hires | 같은 95문항, 이미지당 ≥1024 visual tokens | 95 | 32.6 | 37.9 | +5.3 | 11 / 6 | 0.332 | 2225 | 5 |
| p6_sym_describe | 같은 95문항, "이미지 먼저 옮겨 적기" | 95 | 32.6 | 45.3 | +12.6 | 22 / 10 | 0.050 | 10226 | 25 |
| lora_smoke_eval | LoRA 30step 병합 ckpt, 2과목 | 60 | 68.3 | 46.7 | -21.7 | 4 / 17 | 0.0072 | 2 | 0 |

(원본: `experiments/proposal_table.md`, 이미지 유형별 표: `evidence/03_by_image_type.md`)

## 3. 실험별 해석

### 3.1 생성 설정이 점수를 얼마나 바꾸나 (baseline 준비 단계, `results/`, `log/`)
- 해상도(`min/max_pixels`) 를 기본값 → 256–1280 token으로 줄여도 정확도 59.3 → 59.2%로 같고 시간은 약 34% 단축 (1015s → 673s, 900문항 기준).
- `max_new_tokens` 4096 → 32768: 4096에서 124문항이 잘렸고 그중 92문항이 오답. 공식 recipe(32768)로 되돌리면 58.6 → 61.1%지만 시간이 약 10배(약 3.7시간).
- 따라서 공식 67.4와의 격차 6.3%p 중 일부(2.5%p, 58.6 → 61.1)는 토큰 예산·해상도 설정 때문이고, 나머지는 설정으로 설명되지 않았습니다.

### 3.2 노이즈 기준선 (`p1_noise_seed1234`, `abl_temp0`)
- seed만 바꿔도 -1.0%p, 59문항이 뒤집힘 → **±1~2%p 차이는 개선/악화로 해석하지 않음.**
- temperature 0 (결정적) 은 58.6%로 오히려 낮고 p=0.0059. 길이 초과가 94건(baseline 40건)으로 늘어나 반복 루프에 더 잘 빠지는 것으로 보임. 다만 `presence_penalty=1.5` 를 유지한 설정이라 "greedy 일반"으로 확대 해석하면 안 됨.

### 3.3 서술형 즉답 프롬프트 (`abl_cot_open`) — 가장 확실한 효과
- 서술형 53문항에서 17.0 → 39.6%. W→C 15 / C→W 3, p=0.0075, 같은 문항의 seed 노이즈는 net -1에 불과해 노이즈로 설명되지 않음.
- 특히 Tables 12.5 → 62.5% (+8문항). `Answer the question using a single word or phrase.` 지시가 계산이 필요한 문제에서 실력을 가리고 있었음.
- 한계: n=53으로 작고, 객관식에는 검증하지 않았음.

### 3.4 기호·도식 이미지(95문항) 원인 분리 실험 (p3–p6)
이미지 유형 4종(Sheet Music, Chemical Structures, Sketches and Drafts, Technical Blueprints)은 baseline 32.6%(무작위 기대치 25%)이고 **응답의 66%가 10토큰 이하**의 즉답입니다. 즉답 중 정답률도 33.3%.

| 실험 | 질문 | 결과 | 읽는 법 |
|---|---|---|---|
| p4 텍스트 전용 | 이미지를 실제로 쓰고 있나 | 32.6 → 24.2 (p=0.13) | 이미지를 빼면 떨어지는 방향이지만 유의하지 않음. Sketches 28.6 → 7.1, Chemical 29.0 → 22.6로 일부는 그림을 쓰고 있음 |
| p3 단계별 풀이 | 추론 형식 문제인가 | 32.6 → 40.0 (p=0.23) | 유의하지 않음. Chemical +5, Sketches +5이나 Sheet Music은 -3 |
| p5 고해상도 | 해상도 병목인가 | 32.6 → 37.9 (p=0.33) | 유의하지 않음. Chemical +3, Sketches +3 |
| p6 먼저 설명 후 풀이 | 인식 vs 추론 | 32.6 → **45.3** (p=0.050) | 이 중 가장 큼. Blueprints 40→55, Sheet Music 33→40, Sketches 29→64. 경계선 유의 |

**결론(조심해서 읽기)**
1. 95문항 단일 run, p6도 p≈0.05라 "확정"이 아니라 **방향성**입니다.
2. 네 개 모두 baseline보다 높거나(p3, p5, p6) 이미지 제거 시 낮아져(p4), 문제가 "이미지를 전혀 못 봄"은 아니며 **즉답이 능력을 가리는 면이 큼**.
3. 이미지 유형별로 처방이 다름: 화학 구조·스케치는 해상도/풀이 모두 도움, 악보는 풀이만(p3)으로는 오히려 하락하고 "먼저 옮겨 적기"(p6)에서만 상승 → 악보는 인식 단계가 병목일 가능성.
4. 풀이/설명형 프롬프트는 평균 토큰이 9.6k–10.2k로 baseline(2.4k) 대비 4배 이상이고 길이 초과도 23–25건 발생. 비용 대비 효과를 따져야 함.

사례(문항별 모든 run 응답 + 이미지)는 `evidence/04_examples/` 에 있습니다. 예: `Art_Theory_16` 은 baseline `(D) an atrium`(오답, 6토큰) → p5 정답, p6 정답(608토큰).

### 3.5 LoRA 학습 가능성 점검 (`lora_smoke`, `lora_smoke_eval`)
- 목적: 24GB 3090에서 학습이 되는지, "병합 → 같은 파이프라인 평가"가 동작하는지 확인. **성능 개선 실험이 아님.**
- 설정: language 모듈 LoRA r=16, lr 1e-4, grad_accum 4, 30 step, MMMU **dev**(validation 사용 안 함)
- 결과: OOM 0, peak 12.3GB, 2.31 s/step (1k 샘플당 약 0.16시간 추정), 학습 가능성 확인.
- 병합 모델 2과목 평가: 68.3 → 46.7%, **평균 응답 2토큰** — 소량 데이터로 답 형식만 짧게 굳어진(즉답으로 붕괴된) 것으로 보이며, 이 정확도 하락을 모델 품질로 일반화하면 안 됨. 본 학습 시에는 풀이 포함 타깃 + 더 큰 데이터가 필요.

## 4. 실패/중단 run
`failed_engine_start_1/2`(vLLM 엔진 기동 실패), `failed_cot_open_concurrent`·`aborted_temp0_concurrent`(GPU를 다른 실험과 동시에 써서 중단), `aborted_pixels_fallback`(해상도 fallback 중단)은 결과에 포함하지 않았습니다. 동시 실행 금지가 큐(`scripts/run_proposal_experiments.sh`)의 전제가 된 이유입니다. 로그 일부는 `experiments/aborted_pixels_fallback/`.

## 5. 재현
```bash
source /data/jinagg/env.sh
bash scripts/run_baseline_modelcard.sh --gpu 0 --run_name baseline_modelcard_v1
bash scripts/run_proposal_experiments.sh            # p3~p6, lora, p1, temp0 순차 실행
python code/compare_runs.py --baseline runs/baseline_modelcard_v1 --noise runs/p1_noise_seed1234 \
    runs/abl_cot_open runs/p3_sym_cot runs/p4_sym_textonly runs/p5_sym_hires runs/p6_sym_describe runs/abl_temp0
```
각 `experiments/<run>/command.txt` 에 실제 실행 커맨드, `manifest.json` 에 환경·샘플링 값이 기록되어 있습니다.

## 6. 폴더 안내
| 경로 | 내용 |
|---|---|
| `experiments/<run>/` | 실험별 metrics, manifest, command, summary, 압축 predictions/log |
| `experiments/proposal_table.md` | 위 비교표 원본, `proposal_queue.log` 실행 타임라인 |
| `evidence/` | 제안서용 증거: 헤드라인 수치, 비교표, 유형별 정확도, 문항 사례(이미지 포함), 길이 초과 목록 |
| `docs/proposal_experiments.md` | 각 실험의 설계 의도와 해석 기준 |

올리지 않은 것: LoRA 어댑터 가중치(127MB), GPU 시계열 CSV, 중복 환경 덤프.
