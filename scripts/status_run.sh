#!/usr/bin/env bash
# Quick status of a (running or finished) run directory.
#   bash scripts/status_run.sh [runs/<name>]   (default: newest in runs/)
set -uo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${1:-}"
if [[ -z "$RUN_DIR" ]]; then
  RUN_DIR=$(ls -dt "$REPO_DIR"/runs/*/ 2>/dev/null | head -1)
  [[ -z "$RUN_DIR" ]] && { echo "no runs/ directory yet"; exit 1; }
fi
RUN_DIR="${RUN_DIR%/}"
echo "run dir : $RUN_DIR"
[[ -f "$RUN_DIR/env.txt" ]] && grep -E "started|finished|exit_status" "$RUN_DIR/env.txt"

if [[ -f "$RUN_DIR/pid" ]]; then
  PID=$(cat "$RUN_DIR/pid")
  if kill -0 "$PID" 2>/dev/null; then
    echo "process : RUNNING (pid $PID, $(ps -o etime= -p "$PID" | xargs) elapsed)"
  else
    echo "process : not running (pid $PID)"
  fi
fi

if [[ -d "$RUN_DIR/per_subject" ]]; then
  n=$(ls "$RUN_DIR"/per_subject/*.jsonl 2>/dev/null | wc -l)
  echo "subjects: $n / 30 checkpointed"
fi

python3 - "$RUN_DIR" <<'PY'
import json, sys, os
d = sys.argv[1]
for name in ["metrics.json", "metrics_partial.json"]:
    p = os.path.join(d, name)
    if os.path.exists(p):
        m = json.load(open(p))
        print(f"{name}: status={m.get('status')} overall={m.get('overall_percent', 0):.2f}% "
              f"n={m.get('num_results')} subjects={m.get('num_subjects')}")
        g = m.get("generation", {})
        if g:
            print(f"  finish_reason={g.get('finish_reason')} pred_none={g.get('prediction_none')} "
                  f"tok_mean={g.get('completion_tokens',{}).get('mean')}")
        st = m.get("subject_timing", {})
        if st:
            tot = sum((v.get("seconds") or 0) for v in st.values())
            print(f"  subject time so far: {tot/60:.1f} min over {len(st)} subjects")
        break
PY

echo "--- GPU now ---"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null
echo "--- last log lines ---"
[[ -f "$RUN_DIR/run.log" ]] && grep -v "Processed prompts\|Building prompts\|it/s" "$RUN_DIR/run.log" | tail -15
