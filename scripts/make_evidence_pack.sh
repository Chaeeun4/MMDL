#!/usr/bin/env bash
# Build the proposal evidence pack from finished runs and tar it for download.
#   source /data/$USER/env.sh && bash scripts/make_evidence_pack.sh
# Result: /data/$USER/evidence_pack.tar.gz  (also keeps the folder /data/$USER/evidence)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
USER="${USER:-$(whoami)}"
OUT="${OUT:-/data/$USER/evidence}"
RUNS=()
for r in runs/abl_cot_open runs/p3_sym_cot runs/p4_sym_textonly runs/p5_sym_hires runs/p6_sym_describe \
         runs/lora_smoke_eval runs/abl_temp0 runs/lora_identity_eval; do
  [[ -f "$r/predictions.jsonl" ]] && RUNS+=("$r")
done
NOISE=""; [[ -f runs/p1_noise_seed1234/predictions.jsonl ]] && NOISE="--noise runs/p1_noise_seed1234"
rm -rf "$OUT"
python code/build_evidence_pack.py --out "$OUT" --baseline runs/baseline_modelcard_v1 $NOISE \
  --runs "${RUNS[@]}" --examples 8 --data_root "${HF_HOME:-$HOME/.cache/huggingface}"
cp runs/lora_smoke/lora_smoke_summary.json "$OUT/05_run_metadata/" 2>/dev/null || true
cp runs/proposal_queue.log "$OUT/05_run_metadata/" 2>/dev/null || true
cp reports/mmmu_baseline_modelcard.md docs/proposal_experiments.md "$OUT/" 2>/dev/null || true
tar czf "/data/$USER/evidence_pack.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
echo "---"; du -sh "$OUT"; ls -lh "/data/$USER/evidence_pack.tar.gz"
