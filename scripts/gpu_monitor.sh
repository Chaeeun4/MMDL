#!/usr/bin/env bash
# Append a GPU time series (CSV) every INTERVAL seconds until killed.
#   bash scripts/gpu_monitor.sh <out.csv> [interval_sec=10]
# Columns: timestamp, gpu index, name, util.gpu %, util.mem %, mem.used MiB, mem.total MiB, temp C, power W
set -u
OUT="${1:?usage: gpu_monitor.sh <out.csv> [interval]}"
INTERVAL="${2:-10}"
if [[ ! -s "$OUT" ]]; then
  echo "timestamp,index,name,util_gpu,util_mem,mem_used_mib,mem_total_mib,temp_c,power_w" > "$OUT"
fi
while true; do
  ts=$(date -Is)
  nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw \
    --format=csv,noheader,nounits 2>/dev/null | sed "s/^/${ts},/" | sed 's/, */,/g' >> "$OUT"
  sleep "$INTERVAL"
done
