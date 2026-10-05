# 제안서용 필수 실험 (run_proposal_experiments.sh)

모든 비교는 `runs/baseline_modelcard_v1` (MMMU val 61.11%, 공식 Qwen recipe)과 **같은 문항끼리** 합니다.
GPU 하나에서 **한 번에 하나씩** 돌아가도록 큐로 묶었습니다.

## 실험 목록과 이유

| 이름 | 무엇을 | 왜 필요한가 (제안서 주장) | 대상 | 예상 시간* |
|---|---|---|---|---|
| (완료) `abl_cot_open` | 서술형에 "단계별 풀이 + Answer:" | 즉답형 지시문이 실력을 가린다 (17.0→39.6%, p≈0.008) | 서술형 53 | 40분 |
| `p3_sym_cot` | 기호·도식 이미지 문항에 풀이 유도 | 풀이로 해결되면 프롬프트/추론 문제, 안 되면 인식 문제 → 파인튜닝 근거 | 95문항** | 1~2시간 |
| `p4_sym_textonly` | 같은 문항에서 이미지를 `[image]` 텍스트로 대체 | 이미지 없이도 비슷하게 맞히면 모델이 그림을 거의 안 쓰고 있다 → 인식 학습 필요 | 95문항 | 10~30분 |
| `p5_sym_hires` | 같은 문항, 이미지당 최소 1024 visual tokens | 화학 이미지는 평균 202 tokens로 작음. 해상도만으로 좋아지는지 | 95문항 | 20~40분 |
| `p6_sym_describe` | "이미지를 먼저 옮겨 적고 풀기" | 응답을 읽어 인식 오류(옮겨 적기부터 틀림)와 추론 오류를 사람이 구분 | 95문항 | 1~2시간 |
| `lora` | LoRA 시험 학습 30 step → 병합 → 병합 모델로 2과목 평가 | 3090 24GB에서 학습 가능한지(메모리, 속도), "체크포인트만 바꿔 같은 파이프라인 평가"가 실제로 되는지 | MMMU **dev** 150 | 30~60분 |
| `p1_noise_seed1234` | baseline 설정 그대로, seed만 변경 | 노이즈 기준선. 이보다 작은 변화는 개선이라 부르지 않음 | 900 | 약 3.7시간 |
| `abl_temp0` | temperature 0 (presence_penalty 1.5 유지) | 결정적 기준값, 샘플링 불안정 주장(예: Music 9) 확인 | 900 | 4시간 이상 |

\* RTX 3090 기준 추정. 풀이형은 문항당 수천 토큰을 쓰므로 길어질 수 있음.
\** `Sheet Music, Chemical Structures, Sketches and Drafts, Technical Blueprints` 중 하나를 포함하는 문항. baseline 정확도 32.6%.

`lora`는 MMMU **dev** split만 씁니다(validation은 평가셋이라 사용 금지). 이 어댑터의 점수는 보고용이 아니고 파이프라인 확인용입니다.

## 실행

```bash
source /data/jinagg/env.sh          # venv 활성화 + LD_LIBRARY_PATH 해제 (필수)
cd ~/MMDL
pip install peft                    # lora 실험에만 필요 (없으면 lora만 건너뜀)
bash scripts/run_proposal_experiments.sh --list
bash scripts/run_proposal_experiments.sh            # 전부, 백그라운드, 순서대로
# 일부만: bash scripts/run_proposal_experiments.sh p3 p4 p5
tail -f runs/proposal_queue.log
```

- 다른 실험을 같이 돌리지 마세요. 큐가 GPU가 빌 때까지 기다리고, 주인 없는 vLLM 엔진만 정리합니다.
- 중간에 끊겨도 같은 명령을 다시 실행하면 완료된 실험은 건너뜁니다.
- 끝나면 `runs/proposal_table.md`에 비교표가 생깁니다. 수동으로도 만들 수 있습니다:

```bash
python code/compare_runs.py --baseline runs/baseline_modelcard_v1 --noise runs/p1_noise_seed1234 \
    runs/abl_cot_open runs/p3_sym_cot runs/p4_sym_textonly runs/p5_sym_hires runs/p6_sym_describe runs/abl_temp0
```

## 결과 해석 기준 (제안서 주장과 연결)

| 결과 | 해석 | 제안서 주장 |
|---|---|---|
| p4(텍스트 전용) ≈ baseline | 그림을 거의 활용 못함 | 기호·도식 **인식** 학습이 필요 |
| p3(풀이) 크게 상승, p5 변화 없음 | 즉답/추론 형식 문제 | "풀이 후 답하기" 형식 학습 |
| p5(고해상도) 상승 | 해상도 병목 | 학습·평가 해상도 정책 조정 (baseline 재측정 필요) |
| p3, p5 모두 변화 없음 | 인식/지식 부족 | 도메인 데이터(RDKit 화학, 악보) LoRA |
| p6 응답에서 옮겨 적기부터 틀림 | 인식 오류 비율 | 오류 유형 비율 표로 제시 |
| lora: OOM 없음, peak < 22GB | 학습 가능 | 1개월 계획의 실현 가능성 |

판정 규칙: **W→C − C→W 가 seed-noise의 net 변화보다 확실히 크고, McNemar p < 0.05** 일 때만 "개선"이라고 씁니다.
