# Runbook — 모델 카드(공식 recipe) 기준 MMMU-val baseline 실행 (jina 브랜치)

이 문서는 `jinagg@203.230.60.196:2222` 같은 **직접 접속하는 GPU 서버**에서
Qwen3-VL-4B-Instruct 를 **Qwen 공식 Instruct generation recipe + 체크포인트 기본 이미지 해상도**로
MMMU validation 900문제 전체를 **백그라운드로** 돌리고, 이후 성능 개선 분석에 쓸 자료를
최대한 많이 남기기 위한 절차입니다.

> 과제 가이드(assignment_guidance.md)와 제출 템플릿(SUBMISSION_TEMPLATE.md)의 요구 항목을
> 모두 커버하도록 산출물이 설계되어 있습니다. 리포트 초안: `reports/mmmu_baseline_modelcard.md`

---

## 0. 이번 run의 설정 (이전 team 제출본과의 차이)

| 항목 | 이전 제출본 (`reports/mmmu_baseline.md`) | **이번 run (model-card 설정)** | 출처 |
|---|---|---|---|
| temperature / top_p / top_k | 0.7 / 0.8 / 20 | 0.7 / 0.8 / 20 | Qwen3-VL README "Evaluation Reproduction → Instruct models" |
| repetition_penalty / presence_penalty | 1.0 / 1.5 | 1.0 / 1.5 | 同上 |
| seed | 3407 | 3407 | 同上 |
| `max_new_tokens` (= `out_seq_length`) | **4096** (시간 절약 위해 축소) | **32768** (공식값) | 同上 |
| `min_pixels` / `max_pixels` | 256·32² / 1280·32² (축소) | **체크포인트 processor 기본값** (`image_processor.size`의 `shortest_edge` / `longest_edge`, 실행 시 자동 해석·기록) | HF 모델 카드 preprocessor_config + README "Pixel Control via Official Processor" |
| 프롬프트 / 파서 | MMMU 공식 스타일 / 공식 eval_utils 변형 | **동일 (변경 없음)** | 비교 가능성 유지 |
| 배치 방식 | 900개 한 번에 | **과목별 30개씩** (과목별 소요 시간 측정 + 체크포인트/재개) | README 과제 요구사항 |

예상 소요 시간: 이전 90문제 실험에서 `max_new_tokens=32768` 일 때 약 28~42 s/문제였으므로
RTX 4090 1장 기준 **약 7~11시간**. 과목별 배치는 긴 출력(최대 32k 토큰)에 꼬리 지연이
붙어 조금 더 걸릴 수 있습니다. 그래서 반드시 백그라운드로 실행합니다.

---

## 1. 서버 접속 및 준비

```bash
ssh jinagg@203.230.60.196 -p2222

# 저장소 (최초 1회)
git clone https://github.com/chaeeun4/MMDL.git && cd MMDL
git fetch origin jina && git checkout jina
# 이미 clone 되어 있으면
cd MMDL && git fetch origin jina && git checkout jina && git pull origin jina

# 가상환경 + 의존성 (최초 1회) — vllm 0.19.1 / torch 2.10 / transformers 5.17 조합이 검증됨
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements-lock.txt        # 정확 재현. 실패하면: pip install -r requirements.txt

# (선택) HF 토큰이 있으면 다운로드 속도/제한 완화
export HF_TOKEN=hf_xxx
# (권장) 모델/데이터 캐시 위치를 용량 넉넉한 곳으로 고정
export HF_HOME=/data/jinagg/hf_cache      # 서버 상황에 맞게. 기본값 ~/.cache/huggingface
```

## 2. GPU 자원 확인 (반드시 먼저)

```bash
bash scripts/check_gpu.sh
```

- "free GPUs" 줄에 나온 번호를 사용합니다 (`export CUDA_VISIBLE_DEVICES=N` 또는 아래 `--gpu N`).
- 다른 사람 프로세스가 올라가 있는 GPU는 피합니다. vLLM은 `gpu_memory_utilization=0.90` 으로
  해당 GPU 메모리의 90%를 **선점**하므로, 공유 GPU에서는 OOM 또는 상대방 OOM을 유발합니다.
- 24 GB 미만 GPU면 `--gpu_memory_utilization` 을 낮추지 말고 **`--max_model_len`을 낮추지도 말고**,
  대신 다른 GPU를 기다리는 편이 결과 비교에 안전합니다 (설정이 달라지면 baseline 비교가 깨짐).
- 80 GB급(A100/H100)이면 그대로 실행하면 되고 훨씬 빨리 끝납니다.

## 3. (권장) 10분짜리 smoke test

```bash
bash scripts/run_baseline_modelcard.sh --smoke --gpu 0
#   → runs/smoke_<ts>/ 에 Accounting, Art 60문제 결과 + summary.md 생성 (max_new_tokens=4096)
tail -f runs/smoke_*/run.log      # 모델 다운로드(≈9 GB) + MMMU 다운로드(≈4 GB)가 여기서 일어남
```

summary.md 가 생성되고 `metrics.json` 에 `"status": "completed"` 가 보이면 OK.

## 4. 본 실행 (백그라운드)

```bash
bash scripts/run_baseline_modelcard.sh --gpu 0 --run_name baseline_modelcard_v1
```

출력 예:

```
launched in background (launcher pid 12345)
run dir : /home/jinagg/MMDL/runs/baseline_modelcard_v1
follow  : tail -f runs/baseline_modelcard_v1/run.log
status  : bash scripts/status_run.sh runs/baseline_modelcard_v1
stop    : kill $(cat runs/baseline_modelcard_v1/pid)
```

`setsid nohup` 으로 띄우므로 **ssh 세션을 끊어도 계속 돕니다**. tmux 를 쓰고 싶으면
`tmux new -s mmmu` 안에서 `--fg` 를 붙여 실행해도 됩니다.

### 모니터링

```bash
bash scripts/status_run.sh runs/baseline_modelcard_v1   # 진행 과목 수, 누적 정확도, ETA, GPU 상태
tail -f runs/baseline_modelcard_v1/run.log               # 과목이 끝날 때마다 한 줄 요약
#   [Accounting] acc=20/30 time=1234.5s tok_max=32768 | done 30/900 running_acc=66.67% elapsed=20.6m eta=598.0m
```

### 중단 / 재개

```bash
kill $(cat runs/baseline_modelcard_v1/pid)                                     # 중단
bash scripts/run_baseline_modelcard.sh --resume --run_name baseline_modelcard_v1 --gpu 0   # 재개
```
완료된 과목(`per_subject/<Subject>.jsonl` 30줄)은 건너뛰고 이어서 돕니다.

## 5. 산출물 (runs/<run_name>/)

| 파일 | 내용 | 용도 |
|---|---|---|
| `predictions.jsonl` | 문항별 전체 기록: 프롬프트 전문, raw 출력, 파싱 결과, 정오답, prompt/completion 토큰 수, finish_reason, logprob 요약(누적/평균/첫 토큰 top-5/최저 토큰), 이미지 원본·리사이즈 크기·visual token 수, vLLM per-request 타이밍, subfield/img_type/difficulty, MMMU 정답 해설 | 오답 분석, 길이·확신도·해상도 상관 분석, fine-tuning 데이터 설계 |
| `per_subject/*.jsonl` | 과목별 체크포인트 | 재개, 과목별 분석 |
| `metrics.json` | 과목별 정확도, Overall(macro), 과목별 소요 시간, finish_reason 분포, 토큰 통계, 문항유형/난이도별 정확도, peak VRAM, 환경 | 리포트 5~7절 |
| `manifest.json` | git sha, 전체 인자, **실제 적용된 min/max_pixels와 그 출처**, 샘플링 설정 및 공식 recipe 일치 여부, 패키지 버전, GPU/driver, 실제 프롬프트 예시 | 리포트 1~3절, 재현성 |
| `summary.md` / `summary.json` | 템플릿 형식 표 + 진단 요약 (자동 생성) | 리포트에 붙여넣기 |
| `run.log` | vLLM 로그 포함 전체 stdout/stderr (KV cache 크기, 처리량, 10초 단위 throughput) | 디버깅, 속도 분석 |
| `gpu_monitor.csv` | 10초 간격 GPU util/VRAM/온도/전력 시계열 | VRAM 실측, 병목 분석 |
| `nvidia-smi_before/after.txt`, `pip_freeze.txt`, `env.txt`, `env_full.txt`, `command.txt`, `git_status.txt`, `git_diff.patch` | 실행 환경 스냅샷 | 재현성 |

## 6. 끝난 뒤 할 일

```bash
bash scripts/status_run.sh runs/baseline_modelcard_v1          # status=completed 확인
cat runs/baseline_modelcard_v1/summary.md                       # 표 확인

# 이전 제출본(4096 토큰, 축소 해상도)과 정오답 전이 비교
python code/summarize_run.py runs/baseline_modelcard_v1 \
    --compare results/opt_predictions_orig.jsonl --title "model-card baseline" \
    --out runs/baseline_modelcard_v1/summary_vs_orig.md

# 기존 분석 스크립트도 그대로 사용 가능 (경로만 바꿔서)
python code/analyze_predictions.py --help

# 리포트 채우기: reports/mmmu_baseline_modelcard.md 의 TBD 를 summary.md 값으로 교체

# 커밋 (predictions.jsonl 이 50 MB 넘으면 gzip 해서 커밋)
ls -lh runs/baseline_modelcard_v1/
gzip -k runs/baseline_modelcard_v1/predictions.jsonl   # 필요 시
git add runs/baseline_modelcard_v1 reports/mmmu_baseline_modelcard.md
git commit -m "Add model-card baseline run baseline_modelcard_v1"
git push origin jina
```

## 7. 자주 나는 문제

| 증상 | 조치 |
|---|---|
| `torch.OutOfMemoryError` 모델 로드 중 | 다른 프로세스가 GPU 점유. `check_gpu.sh` 로 빈 GPU 선택 |
| `ValueError: ... prompt ... longer than the maximum model length` | 특정 문항의 이미지가 매우 큼. 코드가 자동으로 해당 과목을 1문항씩 재시도하고 실패 문항은 `finish_reason=error` 로 기록함 (summary 의 errors 항목 확인) |
| HF 다운로드 429/timeout | `export HF_TOKEN=...` 후 `--resume` 로 재개 |
| `nvidia-smi` 없음/권한 | VRAM 측정만 비고 실행은 됨. 서버 관리자에게 문의 |
| 너무 느림 (ETA > 15h) | 그래도 설정을 바꾸지 말 것 (baseline 의미 상실). GPU 가 더 큰 노드로 옮겨 `--resume` 하거나, 과목을 나눠 두 GPU 에서 `--subjects A,B,...` 로 병렬 실행 후 `per_subject/` 를 한 run_dir 에 모아 `summarize_run.py` 실행 |
