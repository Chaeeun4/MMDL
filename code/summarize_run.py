"""
Summarize an MMMU run directory (or a legacy predictions.jsonl + metrics.json
pair) into a Markdown report fragment that drops straight into
reports/mmmu_baseline*.md, plus a machine-readable summary.json.

    python code/summarize_run.py runs/<name> --out runs/<name>/summary.md
    python code/summarize_run.py --predictions results/x.jsonl --metrics results/x.json
    python code/summarize_run.py runs/A --compare runs/B      # transition table

Sections: environment, per-subject table (acc / time / tokens), overall vs
official 67.4, finish-reason + token statistics, parse failures, breakdown by
question type / difficulty / image type, longest outputs, sample errors.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

OFFICIAL_MMMU_VAL = 67.4

SUBJECTS = [
    "Accounting", "Agriculture", "Architecture_and_Engineering", "Art", "Art_Theory",
    "Basic_Medical_Science", "Biology", "Chemistry", "Clinical_Medicine",
    "Computer_Science", "Design", "Diagnostics_and_Laboratory_Medicine", "Economics",
    "Electronics", "Energy_and_Power", "Finance", "Geography", "History", "Literature",
    "Manage", "Marketing", "Materials", "Math", "Mechanical_Engineering", "Music",
    "Pharmacy", "Physics", "Psychology", "Public_Health", "Sociology",
]


def load_jsonl(p: Path) -> List[Dict[str, Any]]:
    with p.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_json(p: Optional[Path]) -> Dict[str, Any]:
    if p and p.exists():
        return json.load(p.open(encoding="utf-8"))
    return {}


def pct(x: float) -> str:
    return f"{x * 100:.2f}"


def fmt_s(x: Optional[float]) -> str:
    if x is None:
        return "-"
    return f"{x:.0f}s" if x < 600 else f"{x / 60:.1f}m"


def quantiles(vals: List[float]) -> Dict[str, Any]:
    if not vals:
        return {}
    s = sorted(vals)
    q = lambda p: s[min(len(s) - 1, int(p * len(s)))]
    return {"n": len(s), "mean": sum(s) / len(s), "median": statistics.median(s),
            "p90": q(0.9), "p99": q(0.99), "max": s[-1], "min": s[0]}


def summarize(rows: List[Dict[str, Any]], metrics: Dict[str, Any],
              manifest: Dict[str, Any]) -> Dict[str, Any]:
    by_sub: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_sub[r["subject"]].append(r)

    subj_tim = metrics.get("subject_timing", {})
    table = []
    for i, s in enumerate(SUBJECTS, 1):
        items = by_sub.get(s)
        if not items:
            continue
        n = len(items)
        c = sum(bool(r.get("correct")) for r in items)
        toks = [r["completion_tokens"] for r in items if r.get("completion_tokens") is not None]
        table.append({
            "no": i, "subject": s, "num": n, "correct": c, "accuracy": c / n,
            "seconds": subj_tim.get(s, {}).get("seconds"),
            "tok_mean": (sum(toks) / len(toks)) if toks else None,
            "tok_max": max(toks) if toks else None,
            "length_stops": sum(1 for r in items if r.get("finish_reason") == "length"),
            "pred_none": sum(1 for r in items if r.get("prediction") is None),
        })
    accs = [t["accuracy"] for t in table]
    overall = sum(accs) / len(accs) if accs else 0.0
    micro = sum(t["correct"] for t in table) / max(1, sum(t["num"] for t in table))

    def slice_by(key: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in rows:
            groups[str(r.get(key, "") or "")].append(r)
        for k, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            out[k] = {"num": len(items),
                      "correct": sum(bool(r.get("correct")) for r in items),
                      "accuracy": sum(bool(r.get("correct")) for r in items) / len(items)}
        return out

    toks_all = [r["completion_tokens"] for r in rows if r.get("completion_tokens") is not None]
    toks_ok = [r["completion_tokens"] for r in rows if r.get("completion_tokens") is not None and r.get("correct")]
    toks_bad = [r["completion_tokens"] for r in rows if r.get("completion_tokens") is not None and not r.get("correct")]
    ptoks = [r["prompt_tokens"] for r in rows if r.get("prompt_tokens")]
    vis = [sum(im.get("visual_tokens", 0) for im in r.get("images", [])) for r in rows if r.get("images")]

    mc = [r for r in rows if r["question_type"] == "multiple-choice"]
    pred_dist = Counter(r.get("prediction") for r in mc)
    gold_dist = Counter(r.get("gold") for r in mc)

    none_rows = [r for r in rows if r.get("prediction") is None]
    length_rows = [r for r in rows if r.get("finish_reason") == "length"]
    length_wrong = sum(1 for r in length_rows if not r.get("correct"))
    err_rows = [r for r in rows if r.get("error")]

    longest = sorted((r for r in rows if r.get("completion_tokens") is not None),
                     key=lambda r: -r["completion_tokens"])[:10]

    return {
        "num_results": len(rows),
        "num_subjects": len(table),
        "overall_percent": overall * 100,
        "micro_percent": micro * 100,
        "official_percent": OFFICIAL_MMMU_VAL,
        "delta": overall * 100 - OFFICIAL_MMMU_VAL,
        "table": table,
        "by_question_type": slice_by("question_type"),
        "by_difficulty": slice_by("topic_difficulty"),
        "by_img_type": slice_by("img_type"),
        "finish_reason": dict(Counter(r.get("finish_reason") for r in rows)),
        "completion_tokens": quantiles(toks_all),
        "completion_tokens_correct": quantiles(toks_ok),
        "completion_tokens_wrong": quantiles(toks_bad),
        "prompt_tokens": quantiles(ptoks),
        "visual_tokens_per_sample": quantiles(vis),
        "prediction_none": len(none_rows),
        "prediction_none_ids": [r["id"] for r in none_rows][:50],
        "length_stops": len(length_rows),
        "length_stops_wrong": length_wrong,
        "errors": len(err_rows),
        "mc_prediction_distribution": dict(sorted(pred_dist.items(), key=lambda kv: str(kv[0]))),
        "mc_gold_distribution": dict(sorted(gold_dist.items(), key=lambda kv: str(kv[0]))),
        "longest_outputs": [{"id": r["id"], "subject": r["subject"], "tokens": r["completion_tokens"],
                             "finish": r.get("finish_reason"), "correct": r.get("correct")} for r in longest],
        "timing": {
            "elapsed_seconds": metrics.get("elapsed_seconds"),
            "inference_seconds": metrics.get("inference_seconds"),
            "model_load_seconds": metrics.get("model_load_seconds"),
            "subject_seconds_sum": sum((t["seconds"] or 0) for t in table),
        },
        "peak_vram_gb": metrics.get("peak_vram_gb"),
        "sampling": metrics.get("sampling") or manifest.get("sampling"),
        "image_pixels": metrics.get("image_pixels") or manifest.get("resolved", {}),
        "environment": metrics.get("environment") or manifest.get("environment", {}),
        "started_at": metrics.get("started_at") or manifest.get("started_at"),
        "finished_at": metrics.get("finished_at") or manifest.get("finished_at"),
    }


def transitions(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> Dict[str, int]:
    ma = {r["id"]: bool(r.get("correct")) for r in a}
    mb = {r["id"]: bool(r.get("correct")) for r in b}
    c: Counter = Counter()
    for k in ma.keys() & mb.keys():
        c[("C" if ma[k] else "W") + "->" + ("C" if mb[k] else "W")] += 1
    return dict(c)


def to_markdown(s: Dict[str, Any], title: str, compare: Optional[Dict[str, Any]] = None) -> str:
    env = s.get("environment", {}) or {}
    pk = env.get("packages", {}) or {}
    gpus = ", ".join(f"{g['name']} ({g['memory_total_mib'] / 1024:.0f} GB)" for g in env.get("gpus", []))
    samp = s.get("sampling") or {}
    px = s.get("image_pixels") or {}
    L: List[str] = []
    L.append(f"# {title}\n")
    L.append("## 환경 / 재현성\n")
    L.append("| 항목 | 값 |\n|---|---|")
    L.append(f"| 모델 checkpoint | `Qwen/Qwen3-VL-4B-Instruct` (ebb281ec70b05090aa6165b016eac8ec08e71b17) |")
    L.append(f"| 추론 백엔드 | vLLM {pk.get('vllm', '?')} (torch {pk.get('torch', '?')}, transformers {pk.get('transformers', '?')}, qwen-vl-utils {pk.get('qwen-vl-utils', '?')}) |")
    L.append(f"| 사용 GPU | {gpus or '?'} (host `{env.get('hostname', '?')}`, driver {', '.join(sorted({g.get('driver', '?') for g in env.get('gpus', [])})) or '?'}, CUDA {env.get('torch_cuda', '?')}) |")
    vram = s.get("peak_vram_gb")
    L.append(f"| 실측 peak VRAM | {'-' if vram is None else f'{vram:.2f} GB'} |")
    t = s["timing"]
    if t.get("elapsed_seconds"):
        L.append(f"| 총 소요 시간 | {t['elapsed_seconds']:.0f} s ({t['elapsed_seconds'] / 3600:.2f} h) 전체 / 추론 {t.get('inference_seconds', 0):.0f} s / 모델 로드 {t.get('model_load_seconds') or 0:.0f} s |")
    L.append(f"| 실행 시각 | {s.get('started_at')} → {s.get('finished_at')} |")
    L.append(f"| git | `{env.get('git_branch')}` @ `{env.get('git_commit')}` dirty={env.get('git_dirty')} |")
    L.append("")
    L.append("## 생성 설정\n")
    L.append("| 파라미터 | 값 |\n|---|---|")
    for k in ["greedy", "seed", "temperature", "top_p", "top_k", "repetition_penalty",
              "presence_penalty", "max_new_tokens", "logprobs"]:
        L.append(f"| `{k}` | {samp.get(k)} |")
    L.append(f"| `min_pixels` | {px.get('min_pixels')} |")
    L.append(f"| `max_pixels` | {px.get('max_pixels')} |")
    L.append(f"| 공식 recipe 일치 | {samp.get('matches_official_instruct_recipe')} |")
    L.append("")
    L.append("## 결과\n")
    L.append("| No. | Subject | Data Num | Acc | 소요 시간 | 평균 토큰 | 최대 토큰 | length stop | parse 실패 |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in s["table"]:
        L.append(f"| {r['no']} | {r['subject']} | {r['num']} | {pct(r['accuracy'])} | {fmt_s(r['seconds'])} | "
                 f"{r['tok_mean']:.0f} | {r['tok_max']} | {r['length_stops']} | {r['pred_none']} |"
                 if r['tok_mean'] is not None else
                 f"| {r['no']} | {r['subject']} | {r['num']} | {pct(r['accuracy'])} | {fmt_s(r['seconds'])} | - | - | {r['length_stops']} | {r['pred_none']} |")
    L.append(f"|  | **Overall (macro avg)** | **{s['num_results']}** | **{s['overall_percent']:.2f}** | "
             f"{fmt_s(t.get('subject_seconds_sum'))} |  |  | {s['length_stops']} | {s['prediction_none']} |")
    L.append("")
    L.append(f"계산식: `Overall = mean(30개 과목 accuracy)` (= micro {s['micro_percent']:.2f}%, 과목당 30문제로 동일)\n")
    L.append("## 공식 수치와의 비교\n")
    L.append("| | Overall (MMMU val) |\n|---|---|")
    L.append(f"| 공식 (Qwen3-VL Technical Report) | {OFFICIAL_MMMU_VAL} |")
    L.append(f"| 우리 재현 결과 | {s['overall_percent']:.2f} |")
    L.append(f"| 차이 (Δ) | {s['delta']:+.2f} |")
    L.append("")
    L.append("## 생성 진단 (격차 분석용)\n")
    L.append(f"- finish_reason: `{s['finish_reason']}` → length(잘림) {s['length_stops']}건 중 오답 {s['length_stops_wrong']}건")
    L.append(f"- 파싱 실패(prediction=None): {s['prediction_none']}건, 실행 오류: {s['errors']}건")
    ct, co, cw = s["completion_tokens"], s["completion_tokens_correct"], s["completion_tokens_wrong"]
    if ct:
        L.append(f"- completion tokens 전체: mean {ct['mean']:.0f} / median {ct['median']:.0f} / p90 {ct['p90']} / p99 {ct['p99']} / max {ct['max']}")
    if co and cw:
        L.append(f"- completion tokens 정답: median {co['median']:.0f} (mean {co['mean']:.0f}) vs 오답: median {cw['median']:.0f} (mean {cw['mean']:.0f})")
    if s.get("prompt_tokens"):
        pt = s["prompt_tokens"]
        L.append(f"- prompt tokens: mean {pt['mean']:.0f} / max {pt['max']}")
    if s.get("visual_tokens_per_sample"):
        vt = s["visual_tokens_per_sample"]
        L.append(f"- visual tokens/sample: mean {vt['mean']:.0f} / median {vt['median']:.0f} / max {vt['max']}")
    L.append(f"- 객관식 예측 분포: `{s['mc_prediction_distribution']}` vs 정답 분포: `{s['mc_gold_distribution']}`")
    L.append("")
    for key, name in [("by_question_type", "문항 유형"), ("by_difficulty", "난이도"), ("by_img_type", "이미지 유형 (상위)")]:
        d = s.get(key) or {}
        if not d:
            continue
        L.append(f"**{name}별**\n")
        L.append("| 구분 | N | Acc |\n|---|---|---|")
        for k, v in list(d.items())[:12]:
            L.append(f"| {k or '(blank)'} | {v['num']} | {pct(v['accuracy'])} |")
        L.append("")
    if s.get("longest_outputs"):
        L.append("**가장 긴 출력 Top 10**\n")
        L.append("| id | subject | tokens | finish | correct |\n|---|---|---|---|---|")
        for r in s["longest_outputs"]:
            L.append(f"| {r['id']} | {r['subject']} | {r['tokens']} | {r['finish']} | {r['correct']} |")
        L.append("")
    if compare:
        L.append("## 다른 run과의 비교\n")
        L.append(f"- 비교 대상 overall: {compare['overall_percent']:.2f}% (Δ {s['overall_percent'] - compare['overall_percent']:+.2f}p)")
        L.append(f"- 정오답 전이 (this → other): `{compare['transitions']}`")
        L.append("")
    return "\n".join(L)


def resolve_inputs(run_dir: Optional[str], predictions: Optional[str], metrics: Optional[str]):
    if run_dir:
        d = Path(run_dir)
        pred = d / "predictions.jsonl"
        if not pred.exists():
            # Assemble from per-subject checkpoints (run still in progress).
            rows: List[Dict[str, Any]] = []
            for p in sorted((d / "per_subject").glob("*.jsonl")):
                rows.extend(load_jsonl(p))
            met = load_json(d / "metrics_partial.json") or load_json(d / "metrics.json")
        else:
            rows = load_jsonl(pred)
            met = load_json(d / "metrics.json")
        man = load_json(d / "manifest.json")
        return rows, met, man
    rows = load_jsonl(Path(predictions))
    met = load_json(Path(metrics)) if metrics else {}
    return rows, met, {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default=None)
    ap.add_argument("--predictions", default=None)
    ap.add_argument("--metrics", default=None)
    ap.add_argument("--compare", default=None, help="other run dir or predictions.jsonl")
    ap.add_argument("--title", default="MMMU-val run summary")
    ap.add_argument("--out", default=None, help="write markdown here (default: stdout)")
    ap.add_argument("--json", default=None, help="write summary json here")
    args = ap.parse_args()
    if not args.run_dir and not args.predictions:
        ap.error("give a run_dir or --predictions")

    rows, met, man = resolve_inputs(args.run_dir, args.predictions, args.metrics)
    if not rows:
        raise SystemExit("no prediction records found")
    s = summarize(rows, met, man)

    cmp_summary = None
    if args.compare:
        cp = Path(args.compare)
        if cp.is_dir():
            orows, omet, oman = resolve_inputs(str(cp), None, None)
        else:
            orows, omet, oman = load_jsonl(cp), {}, {}
        cmp_summary = {"overall_percent": summarize(orows, omet, oman)["overall_percent"],
                       "transitions": transitions(rows, orows)}
        s["compare"] = {"path": str(cp), **cmp_summary}

    md = to_markdown(s, args.title, cmp_summary)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(md)
    if args.json:
        Path(args.json).write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
