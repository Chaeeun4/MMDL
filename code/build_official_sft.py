"""
SFT data whose PROMPT is the official MMMU evaluation wording (prompt.py MC_DIRECT / OPEN_DIRECT) and
whose RESPONSE is a worked solution ending in 'Answer: X'. The model is evaluated with the unchanged
official prompt, so the reasoning habit has to come from the weights, not from the prompt.

Two sources, usable together:
  --from_sft   existing SFT jsonl (gen_rft.py select output); only the instruction suffix is replaced
  --mfr_dir    MMFineReason-SFT-123K parquet dir (arXiv 2601.21821; solutions written by
               Qwen3-VL-235B-Thinking = external model used for training-data generation only).
               The teacher's final solution (the part after </think>) is kept, the long thinking is dropped.

No MMMU / MMMU-Pro data is used. Every MMFineReason record is checked against MMMU dev/validation/test
and MMMU-Pro (question text: exact / 8-gram; image: dHash against every MMMU image) and hits are dropped.

    python code/build_official_sft.py --from_sft /data/$USER/rft/c1b/sft.jsonl --out_dir /data/$USER/rft/offc1b
    python code/build_official_sft.py --mfr_dir /data/$USER/train_data/MMFineReason-123K --out_dir /data/$USER/rft/offmfr
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompt import DESCRIPT_MC, DESCRIPT_OPEN, MC_DIRECT, OPEN_DIRECT  # noqa: E402

USER = os.environ.get("USER", "user")
# per-source cap; sources not listed (puzzles, games) are skipped because MMMU has nothing like them
QUOTA = {
    "BMMR": 3000, "FineVision-visualwebinstruct(filtered)": 3000, "MMR1": 1500, "MMK12": 800, "ViRL39K": 800,
    "LLaVA-CoT": 800, "FineVision-tqa": 400, "FineVision-ai2d_merged": 200, "FineVision-scienceqa": 150,
    "Zebra-CoT-Physics": 200, "mmopenr1-8k": 300, "WaltonColdStart": 300, "Euclid30K": 250,
    "FineVision-geo170k(qa)": 150, "FineVision-geometry3k(mathv360k)": 100,
    "WeMath2-Pro": 100, "WeMath2-Standard": 100, "WeMath2-SFT": 78,
}
OPTION_RE = re.compile(r"(?:^|[\s(])([A-Ja-j])[.):]\s")
FINAL_RE = re.compile(r"(?:\n|^)[^\n]*<answer>(.*?)</answer>[^\n]*\s*$", re.S)


def retemplate(path):
    """Swap the describe_cot instruction of an existing SFT file for the official one."""
    out = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        p = r["prompt"]
        if p.endswith(DESCRIPT_MC):
            p = p[: -len(DESCRIPT_MC)] + MC_DIRECT
        elif p.endswith(DESCRIPT_OPEN):
            p = p[: -len(DESCRIPT_OPEN)] + OPEN_DIRECT
        else:
            continue
        out.append({"id": r["id"], "images": r["images"], "prompt": p, "response": r["response"],
                    "src": "self", "kind": r.get("agent", "")})
    return out


def mfr_record(r, min_chars, max_chars):
    """One MMFineReason row -> (prompt, response, kind) or None."""
    q = (r["question"] or "").replace("<image>", "").strip()
    t = r["qwen3vl_235b_thinking_response"] or ""
    if not q or "</think>" not in t:
        return None
    post = t.split("</think>")[-1].strip()
    m = FINAL_RE.search(post)
    if not m:
        return None
    tag = " ".join(m.group(1).split())
    body = post[: m.start()].strip().rstrip("-").strip()
    if not (min_chars <= len(body) <= max_chars) or "<answer>" in body or not tag:
        return None
    gold = (r["answer"] or "").strip()
    has_options = len({x.upper() for x in OPTION_RE.findall(q)}) >= 2
    if has_options and re.fullmatch(r"[A-Ja-j]", gold):
        ans, kind = gold.upper(), "mc"
    elif has_options and re.fullmatch(r"\(?[A-Ja-j]\)?\.?", tag):
        ans, kind = re.sub(r"[^A-Za-z]", "", tag).upper(), "mc"
    elif has_options or len(tag) > 80:
        return None  # options present but no letter answer, or an essay-style answer
    else:
        ans, kind = tag, "open"
    q = re.sub(r"\s*Please provide a clear reasoning process before giving the final answer\.?", "", q)
    prompt = f"<image 1>\n{q}\n\n{MC_DIRECT if kind == 'mc' else OPEN_DIRECT}"
    return prompt, f"{body}\n\nAnswer: {ans}", kind


def dhash_bits(img, size=16):
    import numpy as np
    from PIL import Image
    if not isinstance(img, Image.Image):
        img = Image.open(img)
    a = np.asarray(img.convert("L").resize((size + 1, size), Image.BILINEAR), dtype=np.int16)
    return np.packbits((a[:, 1:] > a[:, :-1]).flatten())


def benchmark_index(data_root, cache_path):
    """Text index + image hashes of every MMMU dev/validation/test question (+ MMMU-Pro text)."""
    import numpy as np
    from datasets import load_dataset
    from check_contamination import norm, shingles
    from dataset import DATASET_NAME, DATASET_REVISION, SUBJECTS
    exact, index = {}, defaultdict(set)
    hashes, hash_ids = [], []
    cached = Path(cache_path).exists()
    if cached:
        z = np.load(cache_path, allow_pickle=True)
        hashes, hash_ids = list(z["hashes"]), list(z["ids"])
    for subj in SUBJECTS:
        for split in ("dev", "validation", "test"):
            ds = load_dataset(DATASET_NAME, subj, split=split, revision=DATASET_REVISION, cache_dir=data_root)
            for bid, q, o in zip(ds["id"], ds["question"], ds["options"]):
                t = norm(q + " " + str(o))
                exact.setdefault(t, bid)
                exact.setdefault(norm(q), bid)
                for s in shingles(t):
                    index[s].add(bid)
            if not cached:
                for row in ds:
                    for k in range(1, 8):
                        if row.get(f"image_{k}") is not None:
                            hashes.append(dhash_bits(row[f"image_{k}"]))
                            hash_ids.append(row["id"])
    if not cached:
        np.savez(cache_path, hashes=np.stack(hashes), ids=np.array(hash_ids))
    pro = "loaded"
    try:
        for cfg in ("standard (10 options)", "standard (4 options)"):
            ds = load_dataset("MMMU/MMMU_Pro", cfg, split="test", cache_dir=data_root)
            for bid, q, o in zip(ds["id"], ds["question"], ds["options"]):
                t = norm(q + " " + str(o))
                exact.setdefault(t, f"pro::{bid}")
                for s in shingles(t):
                    index[s].add(f"pro::{bid}")
    except Exception as e:  # MMMU-Pro questions come from MMMU test, which is covered above
        pro = f"not loaded ({type(e).__name__})"
    return exact, index, np.stack(hashes), hash_ids, pro


def load_mfr(mfr_dir, data_root, rng, a):
    import numpy as np
    import pyarrow.parquet as pq
    from check_contamination import norm, shingles

    cols = ["source", "id", "question", "answer", "qwen3vl_235b_thinking_response", "is_consistent", "image"]
    exact, index, bench_h, bench_ids, pro = benchmark_index(data_root, a.hash_cache)
    pop = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint16)
    virl_bad = set()
    if a.virl_contamination and Path(a.virl_contamination).exists():
        virl_bad = set(json.load(open(a.virl_contamination))["flagged"])
    img_dir = Path(mfr_dir) / "images"
    img_dir.mkdir(exist_ok=True)

    seen = Counter()
    cand = defaultdict(list)  # reservoir of (file, row index) per source, so the pick is uniform over the set
    files = sorted(glob.glob(str(Path(mfr_dir) / "data" / "*.parquet")))
    for f in files:
        for j, s in enumerate(pq.read_table(f, columns=["source"]).column("source").to_pylist()):
            if s in QUOTA:
                seen[s] += 1
                cand[s].append((f, j))
    want = defaultdict(set)
    for s, items in cand.items():
        rng.shuffle(items)
        for f, j in items[: int(QUOTA[s] * a.oversample)]:  # oversample: some rows fail the filters below
            want[f].add(j)

    records, drop, flagged, min_bits = [], Counter(), {}, 999
    kept = Counter()
    for f in files:
        if not want[f]:
            continue
        rows = pq.read_table(f, columns=cols).take(sorted(want[f])).to_pylist()
        for r in rows:
            s = r["source"]
            rid = f"mfr::{s}::{r['id']}"
            if kept[s] >= QUOTA[s]:
                continue
            if not r["is_consistent"] or r["image"] is None or not r["image"].get("bytes"):
                drop["inconsistent or no image"] += 1
                continue
            if s == "ViRL39K" and any(str(r["id"]) in b or b in str(r["id"]) for b in virl_bad):
                drop["ViRL39K id already flagged"] += 1
                continue
            rec = mfr_record(r, a.min_chars, a.max_chars)
            if rec is None:
                drop["format / length"] += 1
                continue
            prompt, response, kind = rec
            t = norm(prompt.replace(MC_DIRECT, "").replace(OPEN_DIRECT, ""))
            sh = shingles(t)
            hits = Counter(b for x in sh for b in index.get(x, ()))
            if t in exact:
                flagged[rid] = {"kind": "text exact", "match": exact[t]}
                continue
            if hits and hits.most_common(1)[0][1] / len(sh) >= 0.5:
                flagged[rid] = {"kind": "text 8gram", "match": hits.most_common(1)[0][0]}
                continue
            from PIL import Image
            try:
                img = Image.open(io.BytesIO(r["image"]["bytes"]))
                img.load()
            except Exception:
                drop["unreadable image"] += 1
                continue
            if min(img.size) < 28:
                drop["tiny image"] += 1
                continue
            d = pop[np.bitwise_xor(bench_h, dhash_bits(img)[None, :])].sum(1)
            k = int(d.argmin())
            min_bits = min(min_bits, int(d[k]))
            if d[k] <= a.max_bits:
                flagged[rid] = {"kind": f"image dhash {int(d[k])} bits", "match": bench_ids[k]}
                continue
            path = img_dir / (re.sub(r"[^A-Za-z0-9_.-]", "_", f"{s}_{r['id']}") + ".png")
            if not path.exists():
                img.convert("RGB").save(path)
            kept[s] += 1
            records.append({"id": rid, "images": [str(path)], "prompt": prompt, "response": response,
                            "src": "mfr", "kind": f"{s}/{kind}"})
    report = {"benchmark_images": len(bench_ids), "mmmu_pro_text": pro, "checked_records": len(records) + len(flagged),
              "min_image_distance_bits": min_bits, "max_bits": a.max_bits, "n_flagged": len(flagged), "flagged": flagged,
              "dropped": dict(drop), "available_per_source": dict(seen), "kept_per_source": dict(kept)}
    return records, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from_sft", nargs="*", default=[])
    ap.add_argument("--mfr_dir", default="")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--data_root", default=os.environ.get("HF_HOME", f"/data/{USER}/hf_cache"))
    ap.add_argument("--hash_cache", default=f"/data/{USER}/train_data/mmmu_all_dhash.npz")
    ap.add_argument("--virl_contamination", default=f"/data/{USER}/train_data/ViRL39K/contamination.json")
    ap.add_argument("--min_chars", type=int, default=400)
    ap.add_argument("--max_chars", type=int, default=4000)
    ap.add_argument("--max_bits", type=int, default=10, help="dHash distance (of 256 bits) treated as the same image")
    ap.add_argument("--oversample", type=float, default=1.6)
    ap.add_argument("--n_val", type=int, default=100, help="held-out records per source")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records, report = [], {}
    for p in a.from_sft:
        records += retemplate(p)
    if a.mfr_dir:
        mfr, report = load_mfr(a.mfr_dir, a.data_root, rng, a)
        records += mfr
        json.dump(report, open(out / "contamination_report.json", "w"), indent=1, ensure_ascii=False)

    rng.shuffle(records)
    val, train, n_val = [], [], Counter()
    for r in records:
        if n_val[r["src"]] < a.n_val:
            n_val[r["src"]] += 1
            val.append(r)
        else:
            train.append(r)
    for name, rows in (("train", train), ("val", val)):
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    chars = sorted(len(r["response"]) for r in train)
    stats = {"train": dict(Counter(r["src"] for r in train)), "val": dict(n_val), "train_total": len(train),
             "kinds": dict(Counter(r["kind"] for r in train)),
             "mc_vs_open": dict(Counter("mc" if r["prompt"].endswith(MC_DIRECT) else "open" for r in train)),
             "response_chars": {"median": chars[len(chars) // 2], "p90": chars[int(len(chars) * .9)]},
             "contamination_flagged": report.get("n_flagged"), "args": vars(a)}
    json.dump(stats, open(out / "build_stats.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in stats.items() if k != "args"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
