"""
Side-by-side error sheet: one Markdown file per subject with, for every question, what each run
answered (prediction, right/wrong, tokens, end of the answer, full answer folded).
Made for manual error labeling across fine-tuning stages. MMMU is read for evaluation analysis only.

    python code/error_sheet.py --subjects Chemistry Music --out_dir experiments/cm_ft/error_analysis \
        base=experiments/baseline_modelcard_v1 cm=experiments/cm_final_official c2cm=experiments/c2cm_final_full

Each positional argument is label=run_dir (a directory with predictions.jsonl[.gz]); the first run is the
reference. The pattern in a question heading has one mark per run in that order: O = correct, x = wrong,
- = not covered by that run.
--images also saves the question images to <out_dir>/images/ (needs the MMMU dataset in the HF cache)
and links them from the sheet. --only_wrong keeps questions that at least one run got wrong.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from compare_runs import load


def question_text(prompt_text: str) -> str:
    t = prompt_text.split("<|im_start|>user\n")[-1].split("<|im_end|>")[0]
    n = 0

    def img(_):
        nonlocal n
        n += 1
        return f"<image {n}>"

    return re.sub(r"<\|vision_start\|>(?:<\|image_pad\|>)+<\|vision_end\|>", img, t).strip()


def save_images(subjects, out_dir: Path) -> dict:
    from datasets import load_dataset

    paths = {}
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    for s in subjects:
        for r in load_dataset("MMMU/MMMU", s, split="validation"):
            for k in range(1, 8):
                im = r.get(f"image_{k}")
                if im is not None:
                    name = f"images/{r['id'].replace('validation_', '')}_{k}.png"
                    im = im.convert("RGB")
                    im.thumbnail((1000, 1000))
                    im.save(out_dir / name, optimize=True)
                    paths.setdefault(r["id"], []).append(name)
    return paths


def fence(text: str) -> str:
    return "````text\n" + text.replace("````", "` ` ` `") + "\n````"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="label=run_dir, reference run first")
    ap.add_argument("--subjects", nargs="+", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--only_wrong", action="store_true")
    ap.add_argument("--tail", type=int, default=300, help="characters of the answer end shown in the table")
    ap.add_argument("--max_chars", type=int, default=6000,
                    help="longer answers are cut in the middle (the full text is in predictions.jsonl.gz)")
    a = ap.parse_args()

    runs = [(x.split("=", 1)[0], load(x.split("=", 1)[1])) for x in a.runs]
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    images = save_images(a.subjects, out_dir) if a.images else {}

    for subj in a.subjects:
        ids = sorted({i for _, r in runs for i in r if r[i]["subject"] == subj},
                     key=lambda i: int(i.rsplit("_", 1)[1]))
        mark = lambda r, i: "-" if i not in r else ("O" if r[i]["correct"] else "x")
        pattern = {i: "".join(mark(r, i) for _, r in runs) for i in ids}
        lines = [f"# {subj}: per-question answers by run", "",
                 "Pattern = one mark per run in this order: " + ", ".join(f"`{n}`" for n, _ in runs)
                 + " (O correct, x wrong, - not run).", "",
                 "| run | n | correct | accuracy |", "|---|---|---|---|"]
        for n, r in runs:
            cov = [i for i in ids if i in r]
            c = sum(bool(r[i]["correct"]) for i in cov)
            lines.append(f"| {n} | {len(cov)} | {c} | {c / max(len(cov), 1) * 100:.1f}% |")
        lines += ["", "| pattern | questions |", "|---|---|"]
        for p, k in Counter(pattern.values()).most_common():
            lines.append(f"| `{p}` | {k}: " + ", ".join(i.rsplit("_", 1)[1] for i in ids if pattern[i] == p) + " |")
        lines.append("")

        for i in ids:
            if a.only_wrong and "x" not in pattern[i]:
                continue
            ref = next(r[i] for _, r in runs if i in r)
            lines += [f"## {i.replace('validation_', '')} `{pattern[i]}`", "",
                      f"gold **{ref['gold']}** · {ref['question_type']} · {ref.get('topic_difficulty', '')} · "
                      f"{ref.get('img_type', '')} · {ref.get('subfield', '')}", "",
                      fence(question_text(ref.get("prompt_text", ""))), ""]
            lines += [f"![{p}]({p})" for p in images.get(i, [])] + ([""] if i in images else [])
            lines += ["| run | prediction | correct | tokens | finish | end of answer |", "|---|---|---|---|---|---|"]
            for n, r in runs:
                if i not in r:
                    continue
                x = r[i]
                tail = " ".join(x["prediction_raw"][-a.tail:].split()).replace("|", "\\|")
                pred = str(x["prediction"])[:60].replace("|", "\\|")
                lines.append(f"| {n} | {pred} | {'O' if x['correct'] else 'x'} | {x.get('completion_tokens', '')} | "
                             f"{x.get('finish_reason', '')} | {tail} |")
            lines.append("")
            for n, r in runs:
                if i in r and len(r[i]["prediction_raw"]) > a.tail:
                    raw = r[i]["prediction_raw"]
                    if len(raw) > a.max_chars:
                        raw = (raw[:a.max_chars // 2] + f"\n\n[... {len(raw) - a.max_chars} characters cut ...]\n\n"
                               + raw[-a.max_chars // 2:])
                    lines += [f"<details><summary>{n}: full answer</summary>", "", fence(raw), "",
                              "</details>", ""]
        out = out_dir / f"{subj}.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"wrote {out} ({len(ids)} questions)")


if __name__ == "__main__":
    main()
