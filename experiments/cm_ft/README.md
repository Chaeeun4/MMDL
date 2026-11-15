# 화학·음악 타깃 파인튜닝 (cm) + 교사 풀이 추가 (c2cm)

작성: 이진아 (branch `jina`) · 2026-11-13 ~ 11-15 · RTX 3090 1장

목표는 MMMU 전체 점수를 유지하면서 Chemistry / Music 점수를 올리는 것이었습니다.
**결론: 어느 단계도 베이스라인을 넘지 못했습니다.** 아래는 결과, 원인 분석, 그리고 오답을 직접 볼 수 있는 자료입니다.

MMMU / MMMU-Pro 데이터는 학습에 쓰지 않았습니다. 평가는 MMMU validation 900문항만 했습니다 (MMMU-Pro, test 평가는 아직 없음).

## 1. 결과 (공식 프롬프트, MMMU-val 900)

| 단계 | run | 전체 | Chemistry (30) | Music (30) | 나머지 28과목 (840) |
|---|---|---|---|---|---|
| 1. 베이스라인 | `baseline_modelcard_v1` | 61.1% (550) | 9 | 10 | 531 |
| 2. 화학·음악 파인튜닝 | `cm_final_official` | 61.1% (550) | 12 | 8 | 530 |
| 3. + 교사 풀이 (Claude Sonnet 5.5) | `c2cm_final_full` | 59.7% (537) | 9 | 9 | 519 |

- 2단계 vs 베이스라인: W→C 51 / C→W 51, McNemar p = 1.0
- 3단계 vs 베이스라인: W→C 42 / C→W 55, p = 0.22 (`../c2cm_ft/compare.md`)
- describe_cot 프롬프트로도 같은 그림입니다: `base_describe` 63.2% → `cm_final_full` 63.7% (p = 0.83, Chemistry 12 → 15, Music 10 → 8, `compare.md`)
- 과목당 30문항이라 2~3문제 차이는 seed만 바꿔도 생기는 범위입니다.

**채점 오류 1건 (아직 수정 안 함)**: `Chemistry_28` 은 선택지 문구에 "(A) = …, (B) = …" 가 들어 있어, 베이스라인과 3단계가 정답 (A)를 골랐는데 B로 파싱됐습니다. 정정하면 Chemistry 는 10 / 12 / 10, 베이스라인 전체는 551 입니다. 위 표는 정정 전 수치입니다.

## 2. 학습 설정

| | cm (2단계) | c2cm (3단계) |
|---|---|---|
| 학습 샘플 | 11,307 | 12,419 |
| 구성 | chem_qa 3000, chem_coord 500, music_qa 3000, music_trans 914, replay 3893 | 같은 구성, replay 만 5006 (교사 풀이 포함) |
| 스텝 / 시간 | 706 / 약 2 h | 776 / 2.25 h |

공통: LoRA r16 / α32, 언어 모듈만, lr 1e-4, grad_accum 16, 1 epoch, 120 스텝마다 체크포인트 (`train_args.json`).

- `chem_qa`, `music_qa`: 업로드된 라벨에서 자동 생성한 문제입니다 (`code/build_cm_data.py`). 화학은 원자 수 / 분자식 / 고리 수 / 없는 원소, 음악은 음자리표 / 조표 / 박자표 / 첫 음 / 음정 / 음길이 / 음표 수 / 최고음. 정답 형식은 describe_cot ("그림 설명 → 풀이 → Answer:") 입니다.
- `chem_coord`, `music_trans`: 원본 과제 (분자 그림 → 3D 좌표, 악보 → PrIMuS semantic 토큰).
- `replay`: C1b 의 ViRL39K 자체 풀이 (`../c1_rft/README.md`). c2cm 은 여기에 4B 모델이 못 푼 1,641문제에 대한 Claude 풀이 중 정답인 것을 더했습니다 (`code/gen_teacher.py`, `../c2cm_ft/select_report.json`). 외부 모델은 학습 데이터 생성에만 썼습니다.
- 오염 검사: 텍스트 (exact / 8-gram) 와 이미지 dHash 를 MMMU dev/val/test, MMMU-Pro 와 대조, 적발 0건 (`contamination_report.json`).

학습 자체는 정상입니다. held-out loss 가 chem_qa 2.80 → 0.03, music_qa 2.39 → 0.06 으로 떨어졌고 replay loss 도 내려가 망각 신호는 없습니다 (`ckpt_report.md`). 즉 만든 문제는 배웠는데 MMMU 로 옮겨가지 않았습니다.

## 3. 오답 분석 요약

60문항의 그림과 모델 풀이를 직접 확인한 결과입니다 (판단은 작성자 개인의 것이니 검증 바랍니다).

**음악: 읽기 자체가 옮겨가지 않았습니다.** 파인튜닝 모델은 학습한 틀("The staff begins with … Reading the first notes in order: …")을 그대로 쓰지만 내용이 틀립니다 (`cm_describe` 열 참고).

| 문항 | 실제 그림 | 파인튜닝 모델이 읽은 것 |
|---|---|---|
| Music_3 | 낮은음자리표, E2 와 F#3 | G3, C4 |
| Music_25 | 보표 위 덧줄의 B♭5 와 C6, 조표 없음 | B♭4, D5, 조표 ♭ 1개 |
| Music_28 | 보표 아래 B♭3 과 A♭4 | B♭4, F4 |
| Music_15 | 가온음자리표, 음 1개 | "soprano clef", 음 2개 |

그림에 없는 박자표·조표를 지어내는 경우도 있습니다 (학습 정답이 항상 세 가지를 다 적는 형식이라 생긴 버릇으로 보입니다). PrIMuS 는 한 줄짜리 단선율 악보뿐인데 MMMU 는 유형이 다릅니다.

| MMMU Music 유형 | 문항 | PrIMuS 에 있는가 |
|---|---|---|
| 음 1~2개만 놓고 음이름·음정·음계 (덧줄, 가온음자리표 포함): 3, 5, 10, 14, 15, 18, 25, 26, 28 | 9 | 없음 |
| 리듬·박자 이론 (점음표, 쉼표, 겹박자, 마디 수): 1, 4, 6, 13, 16, 19, 20, 23 | 8 | 일부 (음길이만) |
| 화음·화성 (쌓인 음, 큰보표, 로마숫자): 7, 8, 9, 22, 24 | 5 | 없음 |
| 조성·음계·전조: 2, 17, 27, 30 | 4 | 일부 (조표만) |
| 총보 읽기, 꾸밈음: 11, 12, 21, 29 | 4 | 없음 |

**화학: 묻는 것이 다릅니다.** 원자 수 / 분자식 / 고리 수를 묻는 MMMU 문항은 0개입니다.

| MMMU Chemistry 유형 | 문항 | 베이스라인 정답 |
|---|---|---|
| 입체화학 (R/S, 카이랄 중심, 거울상, 뉴먼·피셔 투영): 4, 5, 7, 12, 14, 17, 19, 20, 29 | 9 | 0 |
| 그래프·도표 읽기 (상평형도, 적정 곡선, 검량선): 6, 11, 15, 18, 22, 23 | 6 | 2 |
| 표·그림 값으로 계산: 10, 13, 24, 25, 27 | 5 | 3 |
| 루이스 구조·분자 모양: 2, 16, 21, 30 | 4 | 1 |
| 유기 반응성·성질: 3, 9, 26, 28 | 4 | 2 (28 정정 시) |
| 생화학·당 분류: 1, 8 | 2 | 2 |

원자 수 세기도 MMMU 그림에서는 틀립니다 (Chemistry_20: 모델 "C 18, O 2, 고리 3" / 실제 C 17, O 3, 고리 5).

그 외: 공식 프롬프트에서는 풀이 없이 답만 내는 경우가 많습니다 (Chemistry_13 "126.2 g", 정답 12.97; Chemistry_25 는 24.3 으로 반올림 차이).

**다음 방향 (제안)**: MMMU 유형에 맞는 그림을 직접 생성 (음 1~2개 + 여러 음자리표·덧줄, 음정·화음·쉼표; RDKit 쐐기 구조식으로 카이랄 중심·R/S; 합성 상평형도·적정 곡선). 유형만 참고하고 MMMU 문제·그림은 쓰지 않습니다. 화학·음악은 900문항 중 60문항이라 과목당 +5문제여도 전체로는 약 +1%p 입니다.

## 4. 오답을 직접 보려면

| 파일 | 내용 |
|---|---|
| `error_analysis/Chemistry.md`, `error_analysis/Music.md` | 문항별로 문제·그림·정답과 5개 run 의 답을 나란히 놓은 시트. 전체 풀이는 접힌 칸 안에 있습니다. 제목의 패턴은 `base, cm, c2cm, base_describe, cm_describe` 순서의 O/x 입니다. |
| `ckpt_report.md`, `../c2cm_ft/ckpt_report.md` | 체크포인트별 held-out loss, Chemistry/Music 정확도, 고쳐진/망가진/계속 틀린 문항 id |
| `../<run>/predictions.jsonl.gz` | 원본 출력 전체 (`prediction_raw`, `prediction`, `gold`, 첫 토큰 logprob) |
| `../cm_step*_cm`, `../c2cm_step*_cm` | 중간 체크포인트의 Chemistry+Music 평가 (cm 은 describe_cot, c2cm 은 공식 프롬프트) |

다른 과목이나 다른 run 조합으로 시트를 만들 때:

```bash
python code/error_sheet.py --subjects Physics Math --out_dir /tmp/sheets --images \
    base=experiments/baseline_modelcard_v1 cm=experiments/cm_final_official c2cm=experiments/c2cm_final_full
```

`--images` 는 HF 캐시에 MMMU 가 있어야 합니다. 빼면 그림 없이 만들어집니다. `--only_wrong` 은 한 run 이라도 틀린 문항만 남깁니다.
과목별 통계와 라벨링용 CSV 는 기존 `code/analyze_subject_errors.py` 를 쓰면 됩니다.

## 5. 재현

```bash
# 2단계 (데이터 구성 → 학습 → 체크포인트별 평가 → 최종 900문항 평가, 같은 명령으로 이어하기 가능)
mkdir -p /data/$USER/rft/cm && setsid nohup bash scripts/run_cm_ft.sh > /data/$USER/rft/cm/queue.log 2>&1 < /dev/null &
# 3단계 (교사 풀이 생성 → 선별 → 위 큐를 공식 프롬프트로 실행). ANTHROPIC_API_KEY 필요
setsid nohup bash scripts/run_c2cm.sh > /data/$USER/rft/c2/queue.log 2>&1 < /dev/null &
```

화학 원본은 `/data/$USER/train_data/chem_labels/labels`, 음악 원본은 `/data/$USER/train_data/primus_training_5000` 에 있어야 합니다 (`code/build_cm_data.py` 의 `--chem`, `--music`). `PROMPT=official BASELINE=runs/baseline_modelcard_v1` 로 2단계도 공식 프롬프트로 평가할 수 있습니다.
