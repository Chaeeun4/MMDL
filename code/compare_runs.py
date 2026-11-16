"""
Compare ablation / fine-tuned runs against the baseline on the SAME questions.

    python code/compare_runs.py --baseline runs/baseline_modelcard_v1 \
        --noise runs/p1_noise_seed1234 \
        runs/p3_sym_cot runs/p4_sym_textonly runs/p5_sym_hires runs/abl_cot_open \
        --out runs/proposal_table.md

For every run it reports, on the question ids that run covered:
  n, baseline acc, run acc, delta, W->C / C->W flips, exact McNemar p-value,
and -- if --noise is given (same settings as baseline, only the seed differs) --
how many flips the noise run produced on the same ids. A run's change is only
credible when it clearly exceeds that seed-only flip count.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path


def load(path: str):
    p = Path(path)
    if p.is_dir():
        for name in ["predictions.jsonl", "predictions.jsonl.gz"]:
            if (p / name).exists():
                p = p / name
                break
        else:  # unfinished run: use per-subject checkpoints
            rows = []
            for f in sorted((Path(path) / "per_subject").glob("*.jsonl")):
                rows += [json.loads(l) for l in open(f, encoding="utf-8")]
            return {r["id"]: r for r in rows}
    op = gzip.open if str(p).endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as f:
        return {r["id"]: r for r in map(json.loads, f)}


def settings(path: str) -> str:
    p = Path(path)
    m = p / "manifest.json" if p.is_dir() else None
    if not m or not m.exists():
        return ""
    man = json.load(open(m))
    s = man.get("sampling", {})
    a = man.get("args", {})
    bits = []
    if man.get("prompt_variant", "official") != "official":
        bits.append(f"prompt={man['prompt_variant']}")
    if a.get("no_images"):
        bits.append("text-only")
    if s.get("temperature") not in (None, 0.7):
        bits.append(f"T={s.get('temperature')}")
    if a.get("seed") not in (None, 3407):
        bits.append(f"seed={a.get('seed')}")
    px = man.get("resolved", {}).get("min_pixels", {})
    if isinstance(px, dict) and px.get("source") == "cli":
        bits.append(f"min_px={px.get('value')}")
    if a.get("model_path") and "Qwen/" not in str(a.get("model_path")):
        bits.append(f"ckpt={Path(a['model_path']).name}")
    for k in ["img_types", "question_types", "subjects"]:
        if a.get(k):
            bits.append(f"{k}={a[k]}")
    return ", ".join(bits) or "baseline settings"


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def compare(base, run, noise=None):
    ids = sorted(set(base) & set(run))
    if not ids:
        return None
    b_ok = sum(bool(base[i]["correct"]) for i in ids)
    r_ok = sum(bool(run[i]["correct"]) for i in ids)
    wc = sum(1 for i in ids if not base[i]["correct"] and run[i]["correct"])
    cw = sum(1 for i in ids if base[i]["correct"] and not run[i]["correct"])
    out = {"n": len(ids), "base": b_ok, "run": r_ok, "wc": wc, "cw": cw,
           "p": mcnemar_exact(wc, cw)}
    if noise is not None:
        nid = [i for i in ids if i in noise]
        out["noise_flips"] = sum(1 for i in nid if bool(base[i]["correct"]) != bool(noise[i]["correct"]))
        out["noise_n"] = len(nid)
        out["noise_net"] = sum(bool(noise[i]["correct"]) for i in nid) - sum(bool(base[i]["correct"]) for i in nid)
    toks = [run[i].get("completion_tokens") or 0 for i in ids]
    out["tok_mean"] = sum(toks) / len(toks)
    out["length"] = sum(1 for i in ids if run[i].get("finish_reason") == "length")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--noise", default=None, help="baseline settings, different seed")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    base = load(a.baseline)
    noise = load(a.noise) if a.noise else None
    lines = ["| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    runs = ([a.noise] if a.noise else []) + [r for r in a.runs if r != a.noise]
    for r in runs:
        try:
            res = compare(base, load(r), None if r == a.noise else noise)
        except FileNotFoundError:
            lines.append(f"| {Path(r).name} | (not found) |||||||||| ")
            continue
        if not res:
            lines.append(f"| {Path(r).name} | (no overlapping ids) |||||||||| ")
            continue
        n = res["n"]
        nf = (f"{res['noise_flips']} (net {res['noise_net']:+d})" if "noise_flips" in res else
              ("— (this is the noise run)" if r == a.noise else "n/a"))
        lines.append(
            f"| {Path(r).name} | {settings(r)} | {n} | {res['base']/n*100:.1f}% | {res['run']/n*100:.1f}% | "
            f"{(res['run']-res['base'])/n*100:+.1f} | {res['wc']} / {res['cw']} | {res['p']:.3g} | {nf} | "
            f"{res['tok_mean']:.0f} | {res['length']} |")
    md = "\n".join(lines)
    md += ("\n\nHow to read: Δ and flips are computed on the questions each run covered. "
           "'seed-noise flips' = how many of those questions changed correctness between the baseline "
           "and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise "
           "and a small McNemar p.\n")
    print(md)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
