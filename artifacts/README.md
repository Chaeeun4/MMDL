# artifacts — 학습 데이터와 LoRA 체크포인트

서버(`/data/jinagg`)에만 있던 학습용 변형 데이터와 최종 LoRA 어댑터를 옮겨 둔 폴더입니다.
GitHub의 파일당 100MB 제한 때문에 큰 파일은 압축하거나 90MB 조각으로 나눴습니다.

## checkpoints/

각 실험의 **최종 LoRA 어댑터**(r16/α32, 베이스 `Qwen/Qwen3-VL-4B-Instruct`)와 학습 로그입니다.

| 폴더 | 실험 | MMMU-val 900 (공식 프롬프트) |
|---|---|---|
| `c1_rft`, `c1b_rft` | C1 다양한 프롬프트 self-RFT (describe_cot 형식) | experiments/c1_rft, c1b_rft 참고 |
| `cm_ft` | Chemistry+Music 타깃 데이터 | 550 |
| `c2cm_ft` | cm + 교사 모델 답변 | 537 |
| `offc1b_ft` | 공식 프롬프트 SFT, 1라운드 자기 답변 (**현재 최고**) | 595 |
| `offmfr_ft` | 공식 프롬프트 SFT, MMFineReason 부분집합 | 521 |
| `offpc_ft` | offc1b + 합성 도표 읽기 데이터 | 571 |
| `pconly_ft` | 합성 도표 읽기 데이터만 (실수로 생긴 실험) | 478 |
| `offr2_ft` | 1라운드 + 2라운드 자기 답변 | 574 |

복원:

```bash
cd artifacts/checkpoints/offc1b_ft
cat adapter_model.safetensors.part* > adapter_model.safetensors
sha256sum -c SHA256SUMS
```

`adapter_config.json`과 복원한 `adapter_model.safetensors`를 한 폴더에 두면 PEFT 어댑터로 바로 쓸 수 있고,
`code/merge_lora.py`로 베이스에 병합하면 평가에 쓴 모델(8.3GB)이 됩니다.
병합 모델과 중간 step 체크포인트는 크기 때문에 올리지 않았습니다.

## train_data/

모든 `.jsonl`은 gzip으로 압축했습니다(`gunzip -k 파일.jsonl.gz`).
레코드의 `images`는 서버 절대경로이며, 원본 이미지는 포함하지 않았습니다
(ViRL39K, MMFineReason-123K, PrIMuS, 화학 라벨 데이터는 각 출처에서 받아야 합니다).

| 폴더 | 내용 |
|---|---|
| `c1` | 1라운드 생성 결과(`gen`), 선별 결과(`sft`, `dpo`) |
| `c1b` | 1라운드 재선별(`sft`, `dpo`) |
| `c2` | 교사 모델 답변과 선별 결과 |
| `cm`, `c2cm` | Chemistry+Music 혼합 학습/검증 세트 |
| `cm_derived` | 화학·악보 라벨에서 만든 QA와 원 과제 데이터 |
| `offc1b`, `offmfr`, `offpc`, `pconly`, `offr2` | 공식 프롬프트 SFT 각 실험의 `train`/`val` |
| `percept` | 합성 도표 읽기 데이터와 생성 이미지(`images.tar.part*`) |
| `r2` | 2라운드 생성 결과와 선별 결과 |

percept 이미지 복원:

```bash
cd artifacts/train_data/percept
cat images.tar.part* > images.tar && sha256sum -c SHA256SUMS && tar -xf images.tar
```

MMMU / MMMU-Pro 데이터는 어떤 학습 세트에도 들어 있지 않습니다. 각 폴더의
`contamination_report.json`, `build_stats.json`에 중복 검사 결과가 있습니다.
