"""
Per-subject error analysis for an MMMU run (predictions.jsonl[.gz]).

    python code/analyze_subject_errors.py experiments/baseline_modelcard_v1/predictions.jsonl.gz \
        --subjects Music Chemistry Diagnostics_and_Laboratory_Medicine \
        --csv_dir experiments/baseline_modelcard_v1/error_labeling

For every subject it prints:
  * accuracy vs. chance (1/#options) and majority-gold baseline
  * accuracy sliced by question type / subfield / img_type / difficulty
  * answer-letter distribution (gold vs prediction) -> position bias
  * token length of correct vs wrong answers, finish reasons, parse failures
  * confidence analysis from the first-token logprobs saved by run_mmmu.py
    (--logprobs 5): how peaked the model's first-token distribution is for
    right vs wrong answers (flat => guessing, peaked+wrong => confidently wrong)
and writes <csv_dir>/<subject>_wrong.csv with one row per wrong sample
(id, gold, pred, img_type, subfield, tokens, confidence, response tail,
gold explanation) plus empty `error_type` / `note` columns for manual labeling:
  perception | knowledge | reasoning | format_parse | truncation_loop | other
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


def load(path):
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def letter_probs(r):
    """P(letter) for the first generated token, renormalised over the option
    letters present in the saved top-N. Returns {letter: p} or None."""
    top = (r.get("logprob_summary") or {}).get("first_token_top")
    if not top:
        return None
    probs = {}
    for t in top:
        tok = (t.get("token") or "").strip().strip("()")
        if re.fullmatch(r"[A-J]", tok):
            probs[tok] = probs.get(tok, 0.0) + math.exp(t["logprob"])
    z = sum(probs.values())
    return {k: v / z for k, v in probs.items()} if z > 0 else None


def entropy(p):
    return -sum(v * math.log(v) for v in p.values() if v > 0)


def acc(rs):
    return (sum(r["correct"] for r in rs) / len(rs) * 100) if rs else float("nan")


def slice_table(rs, key, top=8):
    g = defaultdict(list)
    for r in rs:
        g[str(r.get(key) or "")].append(r)
    out = []
    for k, v in sorted(g.items(), key=lambda kv: -len(kv[1]))[:top]:
        out.append(f"    {k[:44]:44s} n={len(v):3d} correct={sum(r['correct'] for r in v):3d} acc={acc(v):5.1f}%")
    return "\n".join(out)


def tail(text, n=350):
    t = " ".join((text or "").split())
    return t if len(t) <= n else "..." + t[-n:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions")
    ap.add_argument("--subjects", nargs="+", required=True)
    ap.add_argument("--csv_dir", default=None)
    a = ap.parse_args()
    rows = load(a.predictions)

    for sub in a.subjects:
        rs = [r for r in rows if r["subject"] == sub]
        if not rs:
            print(f"\n!! no rows for {sub}")
            continue
        mc = [r for r in rs if r["question_type"] == "multiple-choice"]
        wrong = [r for r in rs if not r["correct"]]
        print("\n" + "=" * 88)
        print(f"{sub}: {sum(r['correct'] for r in rs)}/{len(rs)} = {acc(rs):.1f}%   "
              f"(±{math.sqrt(0.25 / len(rs)) * 100:.0f}p std. err. at n={len(rs)})")
        print("=" * 88)

        # baselines
        if mc:
            chance = sum(1 / max(2, len(r["options"])) for r in mc) / len(mc) * 100
            gold = Counter(r["gold"] for r in mc)
            maj, cnt = gold.most_common(1)[0]
            print(f"  MC n={len(mc)}  acc={acc(mc):.1f}%  | random-guess {chance:.1f}%  "
                  f"| always-'{maj}' {cnt / len(mc) * 100:.1f}%")
            print(f"  gold letters: {dict(sorted(gold.items()))}")
            print(f"  pred letters: {dict(sorted(Counter(str(r['prediction']) for r in mc).items()))}")
        op = [r for r in rs if r["question_type"] != "multiple-choice"]
        if op:
            print(f"  open n={len(op)}  acc={acc(op):.1f}%")

        for key in ["question_type", "subfield", "img_type", "topic_difficulty"]:
            print(f"  by {key}:\n{slice_table(rs, key)}")

        toks_ok = [r["completion_tokens"] for r in rs if r["correct"]]
        toks_bad = [r["completion_tokens"] for r in wrong]
        mean = lambda x: sum(x) / len(x) if x else float("nan")
        print(f"  tokens: correct mean={mean(toks_ok):.0f}  wrong mean={mean(toks_bad):.0f}  "
              f"| finish={dict(Counter(r['finish_reason'] for r in rs))}  "
              f"| parse-None={sum(r['prediction'] is None for r in rs)}")
        vt = [sum(i.get("visual_tokens", 0) for i in r.get("images", [])) for r in rs]
        print(f"  visual tokens/sample: mean={mean(vt):.0f} min={min(vt)} max={max(vt)}")

        # confidence from first-token distribution (MC only)
        conf = []
        for r in mc:
            p = letter_probs(r)
            if p:
                conf.append((max(p.values()), entropy(p), r["correct"], len(p)))
        if conf:
            hi = [c for c in conf if c[0] >= 0.9]
            lo = [c for c in conf if c[0] < 0.6]
            mid = [c for c in conf if 0.6 <= c[0] < 0.9]
            f = lambda xs: (f"n={len(xs):2d} acc={sum(c[2] for c in xs) / len(xs) * 100:5.1f}%" if xs else "n= 0")
            print(f"  first-token confidence (top letter prob): "
                  f"mean right={mean([c[0] for c in conf if c[2]]):.2f} wrong={mean([c[0] for c in conf if not c[2]]):.2f}")
            print(f"    p>=0.9 (confident): {f(hi)} | 0.6-0.9: {f(mid)} | <0.6 (guessing): {f(lo)}")
            cw = [c for c in hi if not c[2]]
            print(f"    confidently wrong (p>=0.9 and wrong): {len(cw)} of {len(wrong)} wrong MC")

        # labeling sheet
        if a.csv_dir:
            d = Path(a.csv_dir)
            d.mkdir(parents=True, exist_ok=True)
            path = d / f"{sub}_wrong.csv"
            with path.open("w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh)
                w.writerow(["id", "question_type", "gold", "prediction", "subfield", "img_type", "difficulty",
                            "completion_tokens", "finish_reason", "top_letter_prob", "n_images",
                            "visual_tokens", "response_tail", "gold_explanation",
                            "error_type", "note"])
                for r in wrong:
                    p = letter_probs(r)
                    w.writerow([r["id"], r["question_type"], r["gold"], r["prediction"], r["subfield"],
                                r["img_type"], r["topic_difficulty"], r["completion_tokens"], r["finish_reason"],
                                f"{max(p.values()):.2f}" if p else "", r.get("num_images"),
                                sum(i.get("visual_tokens", 0) for i in r.get("images", [])),
                                tail(r["prediction_raw"]), tail(r.get("explanation", ""), 500), "", ""])
            print(f"  -> wrote {path} ({len(wrong)} rows)")


if __name__ == "__main__":
    main()
