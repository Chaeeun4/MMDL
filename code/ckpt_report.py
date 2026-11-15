"""
Checkpoint report for error analysis: for every evaluated checkpoint of one fine-tuning run,
held-out loss per data source, Chemistry / Music accuracy on MMMU-val (evaluation only), and
which questions flipped against the base model under the same prompt.

    python code/ckpt_report.py --name cm --ckpt /data/$USER/ckpt/cm_ft --out /data/$USER/rft/cm/ckpt_report.md
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from compare_runs import load

FOCUS = ("Chemistry", "Music")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="eval runs are runs/<name>_step<N>_cm and runs/<name>_final_full")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--baseline", default="runs/base_describe")
    ap.add_argument("--runs_dir", default="runs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    base = load(a.baseline)
    val = {}
    vl = Path(a.ckpt) / "val_log.jsonl"
    if vl.exists():
        for line in open(vl):
            r = json.loads(line)
            val[r["step"]] = r["val_loss"]
    final_step = max(val) if val else None

    runs = []
    for d in sorted(Path(a.runs_dir).glob(f"{a.name}_*")):
        m = re.fullmatch(rf"{re.escape(a.name)}_step(\d+)_cm", d.name)
        if m:
            runs.append((int(m.group(1)), d))
        elif d.name == f"{a.name}_final_full":
            runs.append((final_step or 10 ** 9, d))
    runs.sort()

    srcs = sorted({k for v in val.values() for k in v})
    lines = [f"# Checkpoint report: {a.name}", "",
             "Held-out loss (lower is better; `replay` rising = forgetting of the general data).", "",
             "| step | " + " | ".join(srcs) + " |", "|---|" + "---|" * len(srcs)]
    for s in sorted(val):
        lines.append(f"| {s} | " + " | ".join(f"{val[s].get(k, float('nan')):.3f}" for k in srcs) + " |")
    lines += ["", "MMMU-val accuracy on the same questions, base model vs checkpoint (30 questions per subject, "
              "sampled decoding: a difference of 2-3 questions is within noise).", "",
              "| checkpoint | subject | n | base | ckpt | W→C | C→W |", "|---|---|---|---|---|---|---|"]
    detail = []
    for step, d in runs:
        try:
            run = load(str(d))
        except FileNotFoundError:
            continue
        for subj in FOCUS + ("ALL",):
            ids = sorted(i for i in run if i in base and (subj == "ALL" or run[i]["subject"] == subj))
            if not ids or (subj == "ALL" and len(ids) <= 60):
                continue
            b = sum(bool(base[i]["correct"]) for i in ids)
            r = sum(bool(run[i]["correct"]) for i in ids)
            wc = [i for i in ids if not base[i]["correct"] and run[i]["correct"]]
            cw = [i for i in ids if base[i]["correct"] and not run[i]["correct"]]
            lines.append(f"| {d.name} | {subj} | {len(ids)} | {b / len(ids) * 100:.1f}% | {r / len(ids) * 100:.1f}% | "
                         f"{len(wc)} | {len(cw)} |")
            if subj != "ALL":
                both_wrong = [i for i in ids if not base[i]["correct"] and not run[i]["correct"]]
                detail += [f"### {d.name} / {subj}", f"- fixed (W→C): {', '.join(wc) or '-'}",
                           f"- broken (C→W): {', '.join(cw) or '-'}", f"- still wrong: {', '.join(both_wrong) or '-'}", ""]
    lines += ["", "## Question ids per checkpoint", "",
              "Full model outputs: `runs/<run>/predictions.jsonl` (fields `prediction_raw`, `prediction`, `gold`).", ""]
    Path(a.out).write_text("\n".join(lines + detail), encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
