#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# GPU / environment pre-flight check for the MMMU baseline.
#
#   bash scripts/check_gpu.sh
#
# Prints: GPUs (name, VRAM total/used/free, utilization), processes currently
# holding GPU memory, disk space for the HF cache, and python/vllm versions.
# Exit code is 0 even when something looks busy; read the summary at the end.
# ---------------------------------------------------------------------------
set -uo pipefail

echo "================ host ================"
echo "host     : $(hostname)"
echo "date     : $(date -Is)"
echo "user     : $(whoami)"
echo "cwd      : $(pwd)"
echo

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "!! nvidia-smi not found. No NVIDIA driver visible to this shell." >&2
  exit 1
fi

echo "================ nvidia-smi ================"
nvidia-smi
echo

echo "================ per-GPU summary ================"
printf "%-5s %-32s %10s %10s %10s %6s %6s\n" idx name total_MiB used_MiB free_MiB util% temp
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu \
  --format=csv,noheader,nounits | while IFS=',' read -r idx name tot used free util temp; do
  printf "%-5s %-32s %10s %10s %10s %6s %6s\n" "$idx" "$(echo "$name" | xargs)" "$tot" "$used" "$free" "$util" "$temp"
done
echo

echo "================ processes holding GPU memory ================"
procs=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>/dev/null || true)
if [[ -z "$procs" ]]; then
  echo "(none) -- all GPUs idle"
else
  echo "$procs"
  echo
  echo "owners:"
  echo "$procs" | awk -F', ' '{print $2}' | while read -r pid; do
    [[ -z "$pid" ]] && continue
    ps -o pid=,user=,etime=,cmd= -p "$pid" 2>/dev/null | cut -c1-160
  done
fi
echo

echo "================ free GPUs (>= 20 GiB free, no compute process) ================"
busy_uuids=$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader 2>/dev/null | sort -u || true)
free_list=()
while IFS=',' read -r idx uuid free; do
  uuid=$(echo "$uuid" | xargs); free=$(echo "$free" | xargs)
  if ! grep -q "$uuid" <<<"$busy_uuids" && [[ "$free" -ge 20480 ]]; then
    free_list+=("$idx")
  fi
done < <(nvidia-smi --query-gpu=index,gpu_uuid,memory.free --format=csv,noheader,nounits)
if [[ ${#free_list[@]} -eq 0 ]]; then
  echo "none -- pick a GPU manually or wait. (Qwen3-VL-4B bf16 + vLLM needs ~20 GiB with gpu_memory_utilization=0.90)"
else
  echo "CUDA_VISIBLE_DEVICES candidates: ${free_list[*]}"
  echo "suggested: export CUDA_VISIBLE_DEVICES=${free_list[0]}"
fi
echo

echo "================ disk (HF cache + repo) ================"
HF="${HF_HOME:-$HOME/.cache/huggingface}"
echo "HF_HOME  : $HF"
df -h "$HF" 2>/dev/null || df -h "$HOME"
df -h . | tail -1
echo "(model ~9 GB bf16, MMMU val ~4 GB; keep >= 20 GB free)"
echo

echo "================ python env ================"
PY="${PYTHON:-python3}"
echo "python   : $($PY --version 2>&1) ($(command -v $PY))"
$PY - <<'PY' 2>/dev/null || echo "!! vllm / torch not importable in this python -- run: bash scripts/setup.sh"
import importlib
for m in ["torch", "vllm", "transformers", "qwen_vl_utils", "datasets"]:
    try:
        mod = importlib.import_module(m)
        print(f"{m:16s}: {getattr(mod, '__version__', '?')}")
    except Exception as e:
        print(f"{m:16s}: NOT INSTALLED ({type(e).__name__})")
try:
    import torch
    print(f"torch.cuda      : available={torch.cuda.is_available()} devices={torch.cuda.device_count()} cuda={torch.version.cuda}")
except Exception:
    pass
PY
echo
echo "================ tmux / nohup ================"
command -v tmux >/dev/null && echo "tmux: $(tmux -V)" || echo "tmux: not installed (nohup launcher is used by scripts/run_baseline_modelcard.sh anyway)"
