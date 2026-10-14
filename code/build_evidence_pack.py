"""
Build an "evidence pack" for the proposal slides from finished runs.

    python code/build_evidence_pack.py --out /data/$USER/evidence \
        --baseline runs/baseline_modelcard_v1 --noise runs/p1_noise_seed1234 \
        --runs runs/abl_cot_open runs/p3_sym_cot runs/p4_sym_textonly runs/p5_sym_hires \
               runs/p6_sym_describe runs/lora_smoke_eval \
        --examples 6 --data_root $HF_HOME

Writes into --out:
  00_README.md                what each file is
  01_headline_numbers.md      baseline, noise, per-type, confidence, token stats
  02_compare_table.md         same-question comparison of every run vs baseline
  03_by_image_type.md         accuracy per MMMU img_type for every run
  04_examples/<id>/           question, gold, explanation, baseline response,
                              each run's response, and the question image(s)
                              as PNG (needs `datasets` + the MMMU cache)
  05_run_metadata/            metrics.json + manifest.json of every run
  06_length_stops.md          which questions hit the token limit in which run
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_runs import compare, load, mcnemar_exact, settings  # noqa: E402

SYM = ["Sheet Music", "Chemical Structures", "Sketches and Drafts", "Technical Blueprints"]


def pct(c, n):
    return f"{c / n * 100:.1f}%" if n else "-"


def top_letter_prob(r):
    top = (r.get("logprob_summary") or {}).get("first_token_top") or []
    p = {}
    for t in top:
        tok = (t.get("token") or "").strip().strip("()")
        if len(tok) == 1 and "A" <= tok <= "J":
            p[tok] = p.get(tok, 0) + math.exp(t["logprob"])
    z = sum(p.values())
    return max(p.values()) / z if z else None


def tail(text, n=1200):
    t = (text or "").strip()
    return t if len(t) <= n else t[:600] + "\n...\n" + t[-600:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--noise", default=None)
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--examples", type=int, default=6)
    ap.add_argument("--data_root", default=None, help="HF cache, to export question images")
    a = ap.parse_args()

    out = Path(a.out)
    (out / "04_examples").mkdir(parents=True, exist_ok=True)
    (out / "05_run_metadata").mkdir(exist_ok=True)

    base = load(a.baseline)
    noise = load(a.noise) if a.noise else None
    runs = {Path(r).name: load(r) for r in a.runs if Path(r).exists()}
    rows = list(base.values())

    # ---------------- 01 headline numbers ----------------
    L = ["# Headline numbers (baseline run)\n"]
    n = len(rows); c = sum(r["correct"] for r in rows)
    L.append(f"- MMMU validation: **{c}/{n} = {pct(c, n)}** (macro over subjects = micro, 30 q/subject)")
    for qt in sorted({r["question_type"] for r in rows}):
        s = [r for r in rows if r["question_type"] == qt]
        L.append(f"- {qt}: {sum(r['correct'] for r in s)}/{len(s)} = {pct(sum(r['correct'] for r in s), len(s))}")
    fr = Counter(r["finish_reason"] for r in rows)
    L.append(f"- finish_reason: {dict(fr)}; length-stops by subject: "
             f"{dict(Counter(r['subject'] for r in rows if r['finish_reason'] == 'length').most_common(6))}")
    toks = [r["completion_tokens"] for r in rows]
    ok = [r["completion_tokens"] for r in rows if r["correct"]]; bad = [r["completion_tokens"] for r in rows if not r["correct"]]
    L.append(f"- completion tokens: mean {sum(toks) / n:.0f}, median {sorted(toks)[n // 2]}; "
             f"correct mean {sum(ok) / len(ok):.0f} vs wrong mean {sum(bad) / len(bad):.0f}")
    if noise:
        ids = set(base) & set(noise)
        flips = sum(bool(base[i]["correct"]) != bool(noise[i]["correct"]) for i in ids)
        nc = sum(noise[i]["correct"] for i in ids)
        L.append(f"- seed-only rerun: {nc}/{len(ids)} = {pct(nc, len(ids))}, {flips} questions flipped "
                 f"({pct(flips, len(ids))} of questions)")
    sym = [r for r in rows if any(t in r["img_type"] for t in SYM)]
    sc = sum(r["correct"] for r in sym)
    mc = [r for r in sym if r["question_type"] == "multiple-choice"]
    chance = sum(1 / max(2, len(r["options"])) for r in mc) / len(sym) * 100 if sym else 0
    short = [r for r in sym if r["completion_tokens"] <= 10]
    conf = [(top_letter_prob(r), r["correct"]) for r in mc]
    conf = [x for x in conf if x[0] is not None]
    cw = sum(1 for p, ok_ in conf if p >= 0.9 and not ok_); wrong_mc = sum(1 for _, ok_ in conf if not ok_)
    L.append(f"\n## Symbolic-image subset ({' / '.join(SYM)})\n")
    L.append(f"- n={len(sym)}, correct {sc} = {pct(sc, len(sym))}; random-guess expectation {chance:.1f}%")
    L.append(f"- answered in <=10 tokens: {len(short)} ({pct(len(short), len(sym))}), accuracy of those {pct(sum(r['correct'] for r in short), len(short))}")
    L.append(f"- MC wrong answers with first-token prob >= 0.9 (confidently wrong): {cw} of {wrong_mc}")
    for t in SYM:
        s = [r for r in sym if t in r["img_type"]]
        vt = sorted(sum(i.get("visual_tokens", 0) for i in r["images"]) for r in s)
        L.append(f"- {t}: n={len(s)}, acc {pct(sum(r['correct'] for r in s), len(s))}, "
                 f"median visual tokens {vt[len(vt) // 2] if vt else '-'}, <=10-token answers {sum(r['completion_tokens'] <= 10 for r in s)}")
    L.append("\n## Accuracy by image type (all 900)\n\n| img_type | n | acc |\n|---|---|---|")
    g = defaultdict(list)
    for r in rows:
        for t in (eval(r["img_type"]) if r["img_type"].startswith("[") else [r["img_type"]]):
            g[t].append(r["correct"])
    for t, v in sorted(g.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        if len(v) >= 10:
            L.append(f"| {t} | {len(v)} | {pct(sum(v), len(v))} |")
    (out / "01_headline_numbers.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------------- 02 compare table ----------------
    T = ["| run | settings | n | baseline | run | Δ | W→C / C→W | McNemar p | noise flips on same ids | mean tokens | length |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    order = ([a.noise] if a.noise else []) + [r for r in a.runs if Path(r).exists()]
    for r in order:
        name = Path(r).name
        res = compare(base, noise if r == a.noise else runs[name], None if r == a.noise else noise)
        if not res:
            continue
        nn = res["n"]
        nf = f"{res['noise_flips']} (net {res['noise_net']:+d})" if "noise_flips" in res else "—"
        T.append(f"| {name} | {settings(r)} | {nn} | {pct(res['base'], nn)} | {pct(res['run'], nn)} | "
                 f"{(res['run'] - res['base']) / nn * 100:+.1f} | {res['wc']} / {res['cw']} | {res['p']:.3g} | {nf} | "
                 f"{res['tok_mean']:.0f} | {res['length']} |")
    (out / "02_compare_table.md").write_text("# Same-question comparison vs baseline\n\n" + "\n".join(T) + "\n", encoding="utf-8")

    # ---------------- 03 by image type ----------------
    B = ["# Accuracy by image type, baseline vs each run (questions each run covered)\n"]
    for name, run in runs.items():
        ids = set(base) & set(run)
        gg = defaultdict(lambda: [0, 0, 0])
        for i in ids:
            for t in (eval(base[i]["img_type"]) if base[i]["img_type"].startswith("[") else [base[i]["img_type"]]):
                gg[t][0] += 1; gg[t][1] += base[i]["correct"]; gg[t][2] += run[i]["correct"]
        B.append(f"\n## {name}\n\n| img_type | n | baseline | run | Δ (questions) |\n|---|---|---|---|---|")
        for t, (k, b, c2) in sorted(gg.items(), key=lambda kv: -kv[1][0]):
            if k >= 3:
                B.append(f"| {t} | {k} | {pct(b, k)} | {pct(c2, k)} | {c2 - b:+d} |")
    (out / "03_by_image_type.md").write_text("\n".join(B) + "\n", encoding="utf-8")

    # ---------------- 06 length stops ----------------
    S = ["# Questions that hit the token limit\n", "| run | length stops | of which wrong | ids (first 12) |", "|---|---|---|---|"]
    for name, run in [("baseline", base)] + list(runs.items()):
        ls = [r for r in run.values() if r.get("finish_reason") == "length"]
        S.append(f"| {name} | {len(ls)} | {sum(1 for r in ls if not r['correct'])} | "
                 f"{', '.join(r['id'].replace('validation_', '') for r in ls[:12])} |")
    (out / "06_length_stops.md").write_text("\n".join(S) + "\n", encoding="utf-8")

    # ---------------- 04 examples ----------------
    # pick: questions that a diagnostic run fixed (W->C) and that baseline answered in <=10 tokens
    cands = []
    for name, run in runs.items():
        if name.startswith("lora"):
            continue
        for i in set(base) & set(run):
            if not base[i]["correct"] and run[i]["correct"] and base[i]["completion_tokens"] <= 10:
                cands.append((name, i))
    seen, picked = set(), []
    for name, i in sorted(cands, key=lambda x: (x[1].split("_")[1], x[1])):
        if i not in seen and len(picked) < a.examples:
            seen.add(i); picked.append(i)
    img_ok = False
    try:
        if a.data_root:
            from datasets import load_dataset
            from dataset import DATASET_NAME, DATASET_REVISION
            img_ok = True
    except Exception as e:
        print(f"image export disabled: {e}")
    cache = {}
    for i in picked:
        r = base[i]
        d = out / "04_examples" / i.replace("validation_", "")
        d.mkdir(parents=True, exist_ok=True)
        M = [f"# {i}\n", f"- subject: {r['subject']}  | img_type: {r['img_type']} | difficulty: {r['topic_difficulty']}",
             f"- gold: **{r['gold']}**", f"- options: {r['options']}",
             f"\n## Question (as prompted)\n\n```\n{r['prompt_text'].split('<|im_start|>user')[-1].split('<|im_end|>')[0].strip()}\n```",
             f"\n## Gold explanation (MMMU)\n\n{r.get('explanation') or '(none)'}",
             f"\n## Baseline response ({r['completion_tokens']} tokens, {'correct' if r['correct'] else 'WRONG'}, parsed={r['prediction']})\n\n```\n{tail(r['prediction_raw'])}\n```"]
        for name, run in runs.items():
            if i in run:
                x = run[i]
                M.append(f"\n## {name} ({x['completion_tokens']} tokens, {x['finish_reason']}, "
                         f"{'correct' if x['correct'] else 'WRONG'}, parsed={x['prediction']})\n\n```\n{tail(x['prediction_raw'])}\n```")
        (d / "example.md").write_text("\n".join(M) + "\n", encoding="utf-8")
        if img_ok:
            try:
                subj = r["subject"]
                if subj not in cache:
                    cache[subj] = {row["id"]: row for row in load_dataset(DATASET_NAME, subj, split="validation",
                                                                          revision=DATASET_REVISION, cache_dir=a.data_root)}
                row = cache[subj][i]
                for k in range(1, 8):
                    im = row.get(f"image_{k}")
                    if im is not None:
                        im.convert("RGB").save(d / f"image_{k}.png")
            except Exception as e:
                print(f"image export failed for {i}: {e}")

    # ---------------- 05 metadata ----------------
    for r in [a.baseline] + ([a.noise] if a.noise else []) + a.runs:
        p = Path(r)
        if p.is_dir():
            dd = out / "05_run_metadata" / p.name
            dd.mkdir(parents=True, exist_ok=True)
            for f in ["metrics.json", "manifest.json", "command.txt", "summary.md"]:
                if (p / f).exists():
                    shutil.copy(p / f, dd / f)

    (out / "00_README.md").write_text(
        "# Evidence pack for the proposal\n\n"
        "- 01_headline_numbers.md: baseline facts, seed-noise, symbolic-image subset, by image type\n"
        "- 02_compare_table.md: every run vs baseline on the same questions (W→C/C→W, McNemar p)\n"
        "- 03_by_image_type.md: per-image-type accuracy for every run\n"
        "- 04_examples/: one folder per example question: prompt, gold, explanation, every run's response, image PNGs\n"
        "- 05_run_metadata/: metrics/manifest/command of every run (settings, versions, timing, VRAM)\n"
        "- 06_length_stops.md: which questions hit the 32768-token limit in which run\n"
        f"\nExamples chosen: baseline answered in <=10 tokens and wrong; a diagnostic run got it right. {len(picked)} picked.\n",
        encoding="utf-8")
    print(f"evidence pack written to {out}  (examples: {len(picked)}, images: {'yes' if img_ok else 'no'})")


if __name__ == "__main__":
    main()
