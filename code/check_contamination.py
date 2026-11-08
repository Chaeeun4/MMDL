"""
Flag training questions that overlap with MMMU (dev / validation / test) or MMMU-Pro.

The course forbids training on any MMMU or MMMU-Pro data, and web-curated
training sets (ViRL39K, R1-OneVision, ...) may contain copies. This does a
text-level check: exact match after normalisation, and word 8-gram overlap.

    python code/check_contamination.py --train_parquet /data/$USER/train_data/ViRL39K/39Krelease.parquet \
        --out /data/$USER/train_data/ViRL39K/contamination.json

Writes the flagged training ids (to drop) plus the matching benchmark ids.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import DATASET_NAME, DATASET_REVISION, SUBJECTS  # noqa: E402

N = 8  # word n-gram size
TAG_RE = re.compile(r"<image\s*\d*>|\\boxed\{|[^a-z0-9 ]")


def norm(text: str) -> str:
    return " ".join(TAG_RE.sub(" ", text.lower()).split())


def shingles(text: str):
    w = text.split()
    return {" ".join(w[i:i + N]) for i in range(len(w) - N + 1)}


def benchmark_questions(data_root):
    from datasets import load_dataset
    out = []
    for subj in SUBJECTS:
        for split in ("dev", "validation", "test"):
            ds = load_dataset(DATASET_NAME, subj, split=split, revision=DATASET_REVISION, cache_dir=data_root)
            for row in ds:
                out.append((row["id"], row["question"] + " " + str(row["options"])))
    try:  # MMMU-Pro, if reachable
        for cfg in ("standard (10 options)", "standard (4 options)"):
            ds = load_dataset("MMMU/MMMU_Pro", cfg, split="test", cache_dir=data_root)
            for row in ds:
                out.append((f"pro::{row['id']}", row["question"] + " " + str(row["options"])))
    except Exception as e:
        print(f"MMMU-Pro not loaded ({type(e).__name__}: {e}); MMMU only", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_parquet", required=True)
    ap.add_argument("--id_col", default="qid")
    ap.add_argument("--text_col", default="question")
    ap.add_argument("--data_root", default=os.environ.get("HF_HOME"))
    ap.add_argument("--overlap", type=float, default=0.5,
                    help="flag when this fraction of a training question's 8-grams appear in one benchmark item")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import pandas as pd
    bench = benchmark_questions(a.data_root)
    print(f"benchmark items: {len(bench)}")
    exact = {}
    index = defaultdict(set)
    for bid, text in bench:
        t = norm(text)
        exact.setdefault(t, bid)
        for s in shingles(t):
            index[s].add(bid)

    df = pd.read_parquet(a.train_parquet, columns=[a.id_col, a.text_col])
    flagged = {}
    for qid, q in zip(df[a.id_col], df[a.text_col]):
        t = norm(q)
        if t in exact:
            flagged[qid] = {"match": exact[t], "kind": "exact"}
            continue
        sh = shingles(t)
        if not sh:
            continue
        hits = defaultdict(int)
        for s in sh:
            for bid in index.get(s, ()):
                hits[bid] += 1
        if hits:
            bid, h = max(hits.items(), key=lambda kv: kv[1])
            if h / len(sh) >= a.overlap:
                flagged[qid] = {"match": bid, "kind": f"8gram {h}/{len(sh)}"}

    json.dump({"train": a.train_parquet, "n_train": len(df), "n_benchmark": len(bench),
               "n_flagged": len(flagged), "flagged": flagged}, open(a.out, "w"), indent=1)
    print(f"flagged {len(flagged)} / {len(df)} training questions -> {a.out}")


if __name__ == "__main__":
    main()
