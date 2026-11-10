#!/usr/bin/env python3
"""
MMMU 예측 로그 탐색 스크립트 (LLM/API 호출 없음, 로그만 사용)

로그 필드: id, subject, subfield, img_type, topic_difficulty, question_type, gold, options,
prediction, prediction_raw, correct, finish_reason, completion_tokens, prompt_tokens,
logprob_summary, timing, images ... (없는 필드는 알아서 건너뜀)

사용:
  pip install pandas
  python explore_errors.py --log predictions.jsonl --out explore_out
  # 두 run 비교 (맞->틀, 틀->맞 전이표 + McNemar 검정)
  python explore_errors.py --log run_b.jsonl --compare run_a.jsonl --out explore_out
"""
import argparse
import ast
import json
import math
import os
import re

import pandas as pd

LETTERS = set("ABCDEFGHIJ")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 100)


def read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def acc_table(df, col):
    g = df.groupby(col)["correct"].agg(["sum", "count"])
    g.columns = ["correct_n", "n"]
    g["acc%"] = (g["correct_n"] / g["n"] * 100).round(1)
    ci = [wilson(int(s), int(c)) for s, c in zip(g["correct_n"], g["n"])]
    g["ci95_low"] = [round(lo * 100, 1) for lo, _ in ci]
    g["ci95_high"] = [round(hi * 100, 1) for _, hi in ci]
    return g.sort_values("acc%")


def to_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.startswith("["):
        try:
            return ast.literal_eval(v)
        except Exception:
            return [v]
    return [v]


def prepare(rows):
    recs = []
    for r in rows:
        lp = r.get("logprob_summary") or {}
        ft = lp.get("first_token_top") or []
        first_tok = ft[0]["token"].strip() if ft else None
        first_p = math.exp(ft[0]["logprob"]) if ft else None
        n_tok = r.get("completion_tokens") or 0
        fr = r.get("finish_reason")
        if fr == "length":
            rtype = "truncated"
        elif n_tok <= 20:
            rtype = "direct"
        else:
            rtype = "cot"
        imgs = r.get("images") or []
        opts = r.get("options")
        if isinstance(opts, str):
            try:
                opts = ast.literal_eval(opts)
            except Exception:
                opts = None
        resp = str(r.get("prediction_raw", ""))
        recs.append({
            "id": r["id"],
            "subject": r.get("subject"),
            "subfield": r.get("subfield"),
            "img_type": r.get("img_type"),
            "topic_difficulty": r.get("topic_difficulty"),
            "question_type": r.get("question_type"),
            "gold": str(r.get("gold")),
            "prediction": r.get("prediction"),
            "correct": bool(r.get("correct")),
            "n_options": len(opts) if isinstance(opts, list) else None,
            "completion_tokens": n_tok,
            "prompt_tokens": r.get("prompt_tokens"),
            "finish_reason": fr,
            "resp_type": rtype,
            "mean_logprob": lp.get("mean_logprob"),
            "min_token_logprob": lp.get("min_token_logprob"),
            "n_below_m5": lp.get("num_tokens_below_-5"),
            "first_tok": first_tok,
            "first_tok_p": first_p,
            "num_images": r.get("num_images"),
            "visual_tokens": sum((i.get("visual_tokens") or 0) for i in imgs),
            "decode_seconds": (r.get("timing") or {}).get("decode_seconds"),
            "wait_count": len(re.findall(r"\bWait\b", resp)),
            "has_answer_line": bool(re.search(r"(?im)^\W*(?:final\s+)?answer\s*[:：]", resp[-600:])),
            "resp": resp,
        })
    return pd.DataFrame(recs)


def section(title):
    print("\n" + "=" * 8 + f" {title} " + "=" * 8)


def save(df, outdir, name, index=True):
    df.to_csv(os.path.join(outdir, name), index=index, encoding="utf-8-sig")


# ----------------------------------------------------------------------------
def analyze(df, outdir, review_n):
    n, k = len(df), int(df["correct"].sum())
    lo, hi = wilson(k, n)
    section("전체")
    print(f"문제 {n}개, 정답 {k}개, 정확도 {k/n:.2%} (95% CI {lo:.1%} ~ {hi:.1%})")

    section("응답 유형별 (direct<=20토큰 / cot / truncated)")
    t = acc_table(df, "resp_type")
    print(t)
    save(t, outdir, "by_resp_type.csv")

    if df["has_answer_line"].mean() > 0.05:
        section("'Answer:' 최종 줄 형식 준수 (question_type별)")
        g = df.groupby(["question_type", "has_answer_line"])["correct"].agg(["count", "mean"])
        g["mean"] = (g["mean"] * 100).round(1)
        g.columns = ["n", "acc%"]
        print(g)
        save(g, outdir, "answer_line_compliance.csv")
        print("-> has_answer_line=False는 형식을 안 지킨 응답(잘림 포함). strict 채점이면 이쪽은 오답 처리됩니다.")

    tr = df[df["resp_type"] == "truncated"]
    if len(tr):
        mc = tr[tr["n_options"].notna() & (tr["n_options"] > 0)]
        chance = (1 / mc["n_options"]).mean() * 100 if len(mc) else float("nan")
        print(f"\n잘린 응답 {len(tr)}개 중 '정답' {int(tr['correct'].sum())}개 "
              f"({tr['correct'].mean():.1%}); 객관식 우연 수준 기대값 약 {chance:.1f}%")
        print("-> 우연 수준이면 잘린 응답의 '정답'은 운이므로 정확도에서 따로 빼서 보세요.")
        adj = (k - int(tr["correct"].sum())) / n
        print(f"잘린 응답을 모두 오답으로 칠 때 정확도: {adj:.2%}")

    section("응답 길이 구간별 정확도")
    bins = [-1, 16, 512, 2048, 4096, 16384, 10**9]
    labels = ["<=16", "17-512", "513-2048", "2049-4096", "4097-16384", ">16384"]
    d2 = df.assign(len_bin=pd.cut(df["completion_tokens"], bins=bins, labels=labels))
    t = acc_table(d2, "len_bin").reindex(labels).dropna(how="all")
    print(t)
    save(t, outdir, "by_length_bin.csv")

    for col in ["question_type", "topic_difficulty", "subject"]:
        section(f"{col}별 정확도 (낮은 순)")
        t = acc_table(df, col)
        print(t if col != "subject" else t.head(12))
        save(t, outdir, f"by_{col}.csv")

    section("img_type별 정확도 (낮은 순, n>=5)")
    dimg = df.assign(img_type=df["img_type"].map(to_list)).explode("img_type")
    t = acc_table(dimg, "img_type")
    print(t[t["n"] >= 5])
    save(t, outdir, "by_img_type.csv")

    if df["mean_logprob"].notna().any():
        section("확신도(logprob)와 정확도")
        d = df[(df["resp_type"] == "direct") & df["first_tok"].isin(LETTERS) & df["first_tok_p"].notna()]
        if len(d):
            d = d.assign(conf=pd.cut(d["first_tok_p"], [0, 0.5, 0.7, 0.9, 0.99, 1.0001]))
            t = acc_table(d, "conf")
            print("직답: 첫 토큰(선택지 글자) 확률 구간별 정확도")
            print(t)
            save(t, outdir, "calibration_direct.csv")
        c = df[(df["resp_type"] == "cot") & df["mean_logprob"].notna()]
        if len(c) >= 8:
            c = c.assign(q=pd.qcut(c["mean_logprob"], 4, duplicates="drop"))
            t = acc_table(c, "q")
            print("\nCoT: mean_logprob 사분위별 정확도")
            print(t)
            save(t, outdir, "calibration_cot.csv")

    if "decode_seconds" in df and df["decode_seconds"].notna().any():
        section("시간이 많이 든 과목 (decode_seconds 합계)")
        t = df.groupby("subject")["decode_seconds"].sum().sort_values(ascending=False).head(10) / 60
        print(t.round(1).rename("minutes"))

    section("정답 vs 예측 분포 (객관식)")
    mcq = df[df["gold"].isin(LETTERS)]
    if len(mcq):
        ct = pd.crosstab(mcq["gold"], mcq["prediction"].astype(str))
        print(ct)
        save(ct, outdir, "confusion_matrix.csv")
        gd = mcq["gold"].value_counts().sort_index()
        pr = mcq["prediction"].astype(str).value_counts().reindex(gd.index).fillna(0).astype(int)
        print("\n글자별 개수 (정답 / 예측)")
        print(pd.DataFrame({"gold": gd, "pred": pr, "diff": pr - gd}))

    if len(tr):
        section("잘린 응답 상세")
        t = tr.groupby("subject").size().sort_values(ascending=False).head(10)
        print("과목별 잘린 개수 상위:")
        print(t)
        print(f"\n'Wait' 평균 {tr['wait_count'].mean():.1f}회 (잘린 응답)")

    # 읽어 볼 오답 샘플
    wrong = df[~df["correct"]]
    cols = ["id", "subject", "subfield", "img_type", "question_type", "gold", "prediction",
            "completion_tokens", "finish_reason", "mean_logprob"]

    def view(frame):
        out = frame[cols].copy()
        out["resp_head"] = frame["resp"].str.slice(0, 500)
        out["resp_tail"] = frame["resp"].str.slice(-500)
        return out

    nt = wrong[wrong["resp_type"] != "truncated"]
    sample = nt.sample(n=min(review_n, len(nt)), random_state=0)
    save(view(sample), outdir, "wrong_for_reading.csv", index=False)
    save(view(wrong[wrong["resp_type"] == "truncated"]), outdir, "wrong_truncated.csv", index=False)
    print(f"\n직접 읽어 볼 오답 {len(sample)}개 -> wrong_for_reading.csv, 잘린 오답 -> wrong_truncated.csv")


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n * 2
    return min(1.0, p)


def compare(df_b, df_a, outdir):
    m = df_a[["id", "correct"]].merge(df_b[["id", "subject", "question_type", "correct"]], on="id",
                                      suffixes=("_a", "_b"))
    both_right = int((m.correct_a & m.correct_b).sum())
    a_only = int((m.correct_a & ~m.correct_b).sum())
    b_only = int((~m.correct_a & m.correct_b).sum())
    both_wrong = int((~m.correct_a & ~m.correct_b).sum())
    section("두 run 비교 (a=--compare, b=--log)")
    print(f"공통 문제 {len(m)}개")
    print(f"맞->맞 {both_right} / 맞->틀 {a_only} / 틀->맞 {b_only} / 틀->틀 {both_wrong}")
    print(f"정확도 a {m.correct_a.mean():.2%} -> b {m.correct_b.mean():.2%}, "
          f"McNemar 정확검정 p = {mcnemar_exact(a_only, b_only):.3f}")
    print("(맞->틀 + 틀->맞이 많은데 합계 차이가 작으면 run 간 노이즈, 같은 설정이면 변동 폭의 척도)")
    print("\nquestion_type별 비교:")
    for qt, g in m.groupby("question_type"):
        x = int((g.correct_a & ~g.correct_b).sum())
        y = int((~g.correct_a & g.correct_b).sum())
        print(f"  [{qt}] n={len(g)}  a {g.correct_a.mean():.1%} -> b {g.correct_b.mean():.1%}  "
              f"(맞->틀 {x}, 틀->맞 {y}, McNemar p={mcnemar_exact(x, y):.3f})")
    flips = m[m.correct_a != m.correct_b]
    save(flips, outdir, "flipped_questions.csv", index=False)
    print(f"뒤집힌 문제 {len(flips)}개 -> flipped_questions.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--compare", default=None, help="비교할 다른 run의 jsonl (기준 run)")
    ap.add_argument("--out", default="explore_out")
    ap.add_argument("--review-n", type=int, default=100)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    df = prepare(read_jsonl(args.log))
    analyze(df, args.out, args.review_n)
    if args.compare:
        compare(df, prepare(read_jsonl(args.compare)), args.out)
    print(f"\n저장 위치: {args.out}/")


if __name__ == "__main__":
    main()