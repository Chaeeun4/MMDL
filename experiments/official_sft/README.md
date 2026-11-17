# 공식 프롬프트 SFT (offc1b / offmfr / offpc)

작성: 이진아 (branch `jina`) · 2026-11-16 ~ 11-17 · RTX 3090 1장

앞선 cm / c2cm 은 학습 정답이 describe_cot 형식인데 평가는 공식 프롬프트라 형식이 어긋나 있었습니다 (`../cm_ft/README.md`).
여기서는 **학습 프롬프트를 공식 MMMU 문구 그대로 두고 정답을 풀이로 바꿔서**, 공식 프롬프트만 받아도 모델이 스스로 풀이를 쓰도록 학습했습니다.

**결론: 자체 풀이로 학습한 A (offc1b) 가 66.1% 로 베이스라인 61.1% 보다 5.0%p 높습니다 (p = 0.0015). 외부 풀이 (B) 와 그림 읽기 합성 데이터 (C) 는 A 를 넘지 못했습니다.**

MMMU / MMMU-Pro 데이터는 학습에 쓰지 않았습니다. 평가는 MMMU validation 900문항만 했습니다 (MMMU-Pro, test 평가는 아직 없음).

## 1. 결과 (공식 프롬프트, MMMU-val 900)

| | 베이스라인 | A: offc1b | B: offmfr | C: offpc | pconly (사고) |
|---|---|---|---|---|---|
| run | `baseline_modelcard_v1` | `offc1b_final_full` | `offmfr_final_full` | `offpc_final_full` | `pconly_final_full` |
| 학습 데이터 | 없음 | 자체 풀이 3,901 | MMFineReason 풀이 9,974 | A + 그림 읽기 합성 6,319 | 그림 읽기 합성만 12,638 |
| 전체 | 61.1% (550) | **66.1% (595)** | 57.9% (521) | 63.4% (571) | 53.1% (478) |
| 객관식 (847) | 541 | 572 | 506 | 555 | 471 |
| 주관식 (53) | 9 | 23 | 15 | 16 | 7 |
| Chemistry (30) | 9 | 11 | 9 | 12 | 6 |
| Music (30) | 10 | 13 | 15 | 10 | 11 |
| 답변 길이 중간값 (토큰) | 8 | 557 | 675 | 448 | 87 |
| 길이 초과로 끝난 문항 | 40 | 44 | 1 | 32 | 15 |

문항 단위 비교 (W→C = 새로 맞힘, C→W = 새로 틀림, McNemar exact):

| 비교 | W→C | C→W | p |
|---|---|---|---|
| 베이스라인 → A | 119 | 74 | 0.0015 |
| 베이스라인 → B | 105 | 134 | 0.070 |
| 베이스라인 → C | 101 | 80 | 0.14 |
| 베이스라인 → pconly | 108 | 180 | 2.6e-05 |
| A → B | 84 | 158 | 2.3e-06 |
| A → C | 64 | 88 | 0.062 |
| A → pconly | 90 | 207 | 9.1e-12 |

- 참고: seed 만 바꾼 베이스라인 재실행은 W→C 25 / C→W 34 입니다 (`../p1_noise_seed1234`).
- A 는 한 번 학습한 결과입니다. 다른 seed 로 재학습해 보지 않았습니다.
- 과목당 30문항이라 Chemistry / Music 의 2~3문제 차이는 잡음 범위입니다.

## 2. 학습 설정

공통: LoRA r16 / α32, 언어 모듈만, lr 1e-4, grad_accum 16, 1 epoch (`*_ft/train_args.json`). 실행은 `scripts/run_official_sft.sh` (`ARMS="offc1b offmfr offpc"`).

| | A: offc1b | B: offmfr | C: offpc | pconly |
|---|---|---|---|---|
| 스텝 / 시간 | 243 / 0.97 h | 623 / 2.97 h | 638 / 1.77 h | 789 / 1.66 h |
| 기록 | `../offc1b_ft` | `../offmfr_ft` | `../offpc_ft` | `../pconly_ft` |

- **A (offc1b)**: C1b 의 자체 풀이 (4B 모델이 ViRL39K 문제를 풀어 정답인 것만 남긴 것, `../c1b_rft`) 에서 지시문만 공식 문구로 바꿨습니다 (`code/build_official_sft.py --from_sft`). 풀이 내용은 그대로입니다.
- **B (offmfr)**: MMFineReason-SFT-123K (Qwen3-VL-235B-Thinking 이 쓴 풀이, arXiv 2601.21821) 에서 9,974건을 뽑았습니다. MMMU 와 겹칠 가능성이 있는 79건은 뺐습니다 (`../offmfr_ft/contamination_report.json`).
- **C (offpc)**: A 의 3,901건에 그림 읽기 합성 데이터 6,319건 (화학 1,939 + 음악 2,940 + 그래프 1,440) 을 더했습니다. 합성 데이터는 `code/build_percept_data.py` 가 Verovio (악보), RDKit (입체화학), matplotlib (상평형·적정·검량선·표) 로 그립니다. 문제 유형은 val 오답 분석에서 가져왔지만 MMMU 문항이나 그림은 쓰지 않았습니다. dHash 검사에서 1건이 적발되어 뺐습니다 (`percept/contamination_report.json`).

## 3. 왜 B 와 C 는 A 보다 낮은가

아래 해석은 작성자가 일부 표본만 읽고 내린 판단이니 검증 바랍니다.

**B (MMFineReason 풀이).** 풀이가 길어질수록 정답률이 떨어집니다.

| 답변 길이 | 문항 수 | 정답률 |
|---|---|---|
| 300~800 토큰 | 589 | 64% |
| 800~2,000 토큰 | 273 | 45% |
| 2,000 토큰 이상 | 28 | 39% |

틀린 풀이 4건을 읽어 보면, 계산 결과가 선택지에 없을 때 "문제에 오타가 있는 것 같다" 며 가장 가까운 선택지를 억지로 고릅니다 (`Math_22`: 43 을 구하고 132 선택, `Architecture_and_Engineering_4`: 0.200 을 구하고 −0.01 선택).
B 는 LoRA 1 epoch 한 번만 돌렸습니다. 논문 설정 (전체 파인튜닝, lr 1e-5, 3 epoch, 180만 건) 과 다르므로 "우리 설정에서는 안 맞는다" 까지만 말할 수 있습니다.

**pconly (그림 읽기 합성 데이터만).** 합성 데이터의 정답이 두세 문장이라, 모든 과목에서 두세 문장만 쓰고 답하는 버릇이 들었습니다 (답변 길이 중간값 87 토큰). 음악에서 음 1~2개를 읽는 유형은 9문항 중 7개를 맞혔지만 (베이스라인 4, A 5) 화학 입체화학 9문항은 0개였습니다.

**C (A + 합성 데이터).** A 보다 24문제 적게 맞혔고 주관식이 23 → 16 으로 줄었습니다. 답변 길이 중간값도 557 → 448 토큰으로 짧아졌습니다. 짧은 합성 정답이 풀이 습관을 희석했을 가능성이 있지만 오답을 읽어 확인하지는 않았습니다.

## 4. 과목별 정답 수 (각 30문항)

| 과목 | 베이스라인 | A | B | C | pconly |
|---|---|---|---|---|---|
| Accounting | 21 | 23 | 18 | 21 | 18 |
| Agriculture | 17 | 17 | 20 | 15 | 14 |
| Architecture_and_Engineering | 15 | 21 | 12 | 16 | 9 |
| Art | 20 | 19 | 18 | 17 | 20 |
| Art_Theory | 22 | 23 | 18 | 22 | 25 |
| Basic_Medical_Science | 21 | 23 | 24 | 19 | 18 |
| Biology | 16 | 16 | 13 | 15 | 12 |
| Chemistry | 9 | 11 | 9 | 12 | 6 |
| Clinical_Medicine | 21 | 20 | 19 | 19 | 13 |
| Computer_Science | 16 | 19 | 17 | 17 | 10 |
| Design | 23 | 24 | 23 | 20 | 22 |
| Diagnostics_and_Laboratory_Medicine | 11 | 10 | 8 | 10 | 11 |
| Economics | 21 | 25 | 20 | 25 | 19 |
| Electronics | 15 | 13 | 13 | 13 | 8 |
| Energy_and_Power | 19 | 19 | 17 | 20 | 15 |
| Finance | 18 | 22 | 16 | 23 | 14 |
| Geography | 16 | 17 | 15 | 16 | 13 |
| History | 21 | 23 | 20 | 22 | 23 |
| Literature | 24 | 23 | 26 | 24 | 25 |
| Manage | 13 | 20 | 15 | 22 | 15 |
| Marketing | 27 | 25 | 21 | 27 | 19 |
| Materials | 14 | 17 | 12 | 20 | 13 |
| Math | 19 | 18 | 18 | 19 | 18 |
| Mechanical_Engineering | 13 | 15 | 17 | 17 | 12 |
| Music | 10 | 13 | 15 | 10 | 11 |
| Pharmacy | 21 | 26 | 18 | 22 | 14 |
| Physics | 20 | 23 | 15 | 21 | 19 |
| Psychology | 22 | 23 | 20 | 22 | 21 |
| Public_Health | 27 | 27 | 24 | 25 | 18 |
| Sociology | 18 | 20 | 20 | 20 | 23 |

## 5. pconly 가 생긴 경위 (학습 파일 덮어쓰기 사고)

- 2026-11-16 17:07 에 A 의 학습 파일 `/data/jinagg/rft/offc1b/train.jsonl` 이 그림 읽기 데이터로 덮어써졌습니다. 대기열이 도는 중에 `scripts/run_official_sft.sh` 를 고친 것이 원인입니다 (`queue_a.log.gz` 에 `line 35: syntax error` 가 남아 있습니다).
- 그래서 첫 번째 C 실행은 그림 읽기 데이터만 두 번 (12,638건) 들어간 채 학습됐습니다. 이 결과를 `pconly` 로 이름을 바꿔 보관했습니다. `pconly_final_full` 안의 `command.txt`, `summary.md`, `../pconly_ft/compare.md` 에는 실행 당시 이름인 `offpc` 가 그대로 적혀 있습니다.
- **A 의 66.1% 는 영향이 없습니다.** A 의 학습은 덮어쓰기 전에 끝났고, 스텝 수 243 이 3,901 ÷ 16 과 맞습니다.
- A 의 학습 파일을 원본에서 다시 만들고 C 를 올바른 구성 (10,220건) 으로 다시 돌린 것이 `offpc_final_full` 입니다 (`queue_c2.log.gz`).

## 6. 파일 안내

| 위치 | 내용 |
|---|---|
| `../{offc1b,offmfr,offpc,pconly}_final_full` | 900문항 평가: 예측 원본, 지표, 실행 로그 |
| `../{offc1b,offmfr,offpc,pconly}_ft` | 데이터 구성 통계, 학습 설정, 스텝별 loss, 검증 loss, 베이스라인 비교 |
| `percept/` | 그림 읽기 합성 데이터의 구성 통계와 오염 검사 결과 |
| `queue_{a,b,c,c2}.log.gz` | 대기열 로그 (a = A, b = B, c = 잘못 돌아간 C, c2 = 다시 돌린 C) |
| `../c1b_rft`, `../c1b_rft_describe` | A 의 데이터 출처인 C1b 실험의 선별 통계, 학습 기록, describe_cot 평가 (64.3%) |
| `../c2cm_ft/teacher_test` | 교사 모델 비교: 같은 20문제에서 Claude Sonnet 5.5 13, gpt-5.5 10, gpt-5.4-mini 5개 정답 |

모델 가중치 (`/data/jinagg/ckpt/`) 와 학습 데이터 (`/data/jinagg/rft/`) 는 서버에만 있습니다.
