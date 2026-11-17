#!/usr/bin/env bash
# Official-prompt SFT: the training prompt is the official MMMU wording and the target is a worked solution,
# so the fine-tuned model reasons under the unchanged official prompt. Two arms, one after the other:
#   offc1b : the C1b self-generated answers (ViRL39K), only the instruction replaced   -> isolates the format effect
#   offmfr : MMFineReason-SFT-123K subset (solutions by Qwen3-VL-235B-Thinking, arXiv 2601.21821)
#   offpc  : offc1b + synthetic figure-reading data (code/build_percept_data.py: music / chemistry / plots)
#            -> compared with offc1b it isolates the effect of the figure-reading data
# Each arm: build (skipped when present) -> LoRA SFT -> full MMMU-val 900 eval with the official prompt
# -> compare with runs/baseline_modelcard_v1. Rerun the same command to resume.
#
#   setsid nohup bash scripts/run_official_sft.sh > /data/$USER/rft/official_sft.log 2>&1 < /dev/null &
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /data/$USER/env.sh
D="/data/$USER"
ARMS="${ARMS:-offc1b offmfr}"
log() { echo "[$(date '+%F %T')] $*"; }

for arm in $ARMS; do
  W="$D/rft/$arm"
  if [[ ! -f "$W/build_stats.json" ]]; then
    log "build $arm"
    case "$arm" in
      offc1b) python code/build_official_sft.py --from_sft "$D/rft/c1b/sft.jsonl" --out_dir "$W" ;;
      offmfr) python code/build_official_sft.py --mfr_dir "$D/train_data/MMFineReason-123K" --out_dir "$W" ;;
      offpc)
        [[ -f "$D/rft/percept/build_stats.json" ]] || python code/build_percept_data.py --out_dir "$D/rft/percept"
        [[ -f "$D/rft/offc1b/build_stats.json" ]] || python code/build_official_sft.py --from_sft "$D/rft/c1b/sft.jsonl" --out_dir "$D/rft/offc1b"
        mkdir -p "$W"
        cat "$D/rft/offc1b/train.jsonl" "$D/rft/percept/train.jsonl" | shuf --random-source=<(yes) > "$W/train.jsonl"
        cat "$D/rft/offc1b/val.jsonl" "$D/rft/percept/val.jsonl" > "$W/val.jsonl"
        python -c "import json,sys,collections; c=collections.Counter(json.loads(l)['src'] for l in open(sys.argv[1])); json.dump({'train':dict(c),'train_total':sum(c.values())},open(sys.argv[2],'w'),indent=1); print(dict(c))" "$W/train.jsonl" "$W/build_stats.json" ;;
      *) log "unknown arm $arm"; exit 1 ;;
    esac
  fi
  NAME="$arm" PROMPT=official BASELINE=runs/baseline_modelcard_v1 CKPT_EVAL=0 SAVE_EVERY=200 \
      bash scripts/run_cm_ft.sh || log "$arm failed"
done
log "all arms done"
