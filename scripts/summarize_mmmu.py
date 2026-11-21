#!/usr/bin/env python3
"""Combine Music and Chemistry results from local files and the jina Git ref."""

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE_METRICS = "experiments/baseline_modelcard_v1/metrics.json"
SWEEPS = (
    ("60q sweep", "runs/sweep_60q/summary.csv", {"base", "primus_only", "pubchem_only"}),
    ("60q rerun", "runs/sweep_60q_both_rerun/summary_bothrerun.csv", {"both_rerun"}),
)


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )


def warn(message):
    print(message, file=sys.stderr)


def metrics_row(source, run, model, step, prompt, metrics, expected_total):
    subjects = metrics["subjects"]
    total = metrics.get("num_results")
    if total is None:
        total = sum(score["num"] for score in subjects.values())
    if total != expected_total:
        raise ValueError(f"{source}/{run}: expected {expected_total} questions, got {total}")
    counts = []
    for subject in ("Music", "Chemistry"):
        score = subjects[subject]
        if score["num"] != 30:
            raise ValueError(f"{source}/{run}: expected 30 questions for {subject}")
        correct = score.get("correct")
        if correct is None:
            correct = round(score["accuracy"] * score["num"])
        counts.append(correct)
    overall = f"{metrics['overall_accuracy']:.2%}" if total == 900 else "-"
    return source, run, model, step, metrics.get("prompt_variant") or prompt, *counts, overall


def local_rows(base_path):
    for run, filename, models in SWEEPS:
        path = ROOT / filename
        if not path.is_file():
            warn(f"Missing local result: {path}")
            continue
        with path.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                if row["model"] in models:
                    music = round(float(row["music_acc"]) * 30)
                    chem = round(float(row["chem_acc"]) * 30)
                    yield ("local", run, row["model"], int(row["step"]),
                           row["prompt_variant"], music, chem, "-")

    full_runs = (
        ("900q saved", "base", 0, "official", base_path),
        ("900q regrade", "base", 0, "legacy_cot", "runs/1005/regraded/metrics.json"),
        ("900q rerun", "primus_only", 500, "legacy_cot",
         "runs/full_eval/primus_only/step-500/legacy_cot/metrics.json"),
        ("900q saved", "primus_only", 500, "legacy_cot", "results/mmmu_metrics_primus_only.json"),
        ("900q saved", "pubchem_only", 1188, "legacy_cot", "results/mmmu_metrics_pubchem_only.json"),
    )
    for run, model, step, prompt, filename in full_runs:
        path = find_metrics(filename)
        if not path.is_file():
            warn(f"Missing local result: {path}")
            continue
        metrics = json.loads(path.read_text(encoding="utf-8-sig"))
        yield metrics_row("local", run, model, step, prompt, metrics, 900)


def find_metrics(filename):
    path = ROOT / Path(filename).expanduser()
    if not path.is_file() and path.suffix == ".json" and path.with_suffix("").is_file():
        return path.with_suffix("")
    return path


def jina_rows(ref, base_path):
    commit = git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
    if commit.returncode:
        warn(f"Missing Git ref: {ref}")
        return
    commit_id = commit.stdout.strip()

    runs = [
        ("baseline_modelcard_v1", "base", 0, 900),
        ("abl_temp0", "base", 0, 900),
        ("base_describe", "base", 0, 900),
        ("p1_noise_seed1234", "base", 0, 900),
    ]
    for run, model in (
        ("c1_rft_describe", "c1_rft"),
        ("cm_final_full", "cm"),
        ("cm_final_official", "cm"),
        ("c2cm_final_full", "c2cm"),
    ):
        training_run = model if model == "c1_rft" else f"{model}_ft"
        summary = git("show", f"{commit_id}:experiments/{training_run}/train_summary.json")
        step = json.loads(summary.stdout)["steps"] if summary.returncode == 0 else None
        runs.append((run, model, step, 900))
    for model, last_step in (("cm", 600), ("c2cm", 720)):
        runs.extend((f"{model}_step{step}_cm", model, step, 60)
                    for step in range(120, last_step + 1, 120))

    local_base = find_metrics(base_path)
    for run, model, step, total in runs:
        result = git("show", f"{commit_id}:experiments/{run}/metrics.json")
        if result.returncode:
            warn(f"Missing Git result: {ref}/experiments/{run}/metrics.json")
            continue
        metrics = json.loads(result.stdout)
        if run == "baseline_modelcard_v1" and local_base.is_file():
            if metrics == json.loads(local_base.read_text(encoding="utf-8-sig")):
                continue
        yield metrics_row(ref, run, model, step, "official", metrics, total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jina-ref", default="origin/jina", help="Git ref containing jina results")
    args = parser.parse_args()
    base_path = os.environ.get("BASE_OFFICIAL_METRICS", BASE_METRICS)
    rows = [*local_rows(base_path), *jina_rows(args.jina_ref, base_path)]
    rows.sort(key=lambda row: (-(row[5] + row[6]), row[2],
                               -1 if row[3] is None else row[3], row[4], row[1], row[0]))

    headers = ("Source", "Run", "Model", "Step", "Prompt", "Music", "Chem", "M+C", "900q")
    display_rows = [
        (source, run, model, str(step) if step is not None else "-", prompt,
         f"{music}/30", f"{chem}/30", f"{music + chem}/60", overall)
        for source, run, model, step, prompt, music, chem, overall in rows
    ]
    widths = [max(map(len, column)) for column in zip(headers, *display_rows)]
    alignments = ("<", "<", "<", ">", "<", ">", ">", ">", ">")
    fmt = " ".join(f"{{:{align}{width}}}" for align, width in zip(alignments, widths))
    header = fmt.format(*headers)
    print(header)
    print("-" * len(header))
    for row in display_rows:
        print(fmt.format(*row))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
