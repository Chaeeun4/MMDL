#!/usr/bin/env python3
"""
MMMU 오답 유형 분류 파이프라인 (OpenAI API 버전)

1) 로그(jsonl)에서 오답만 추림
2) 규칙으로 먼저 분류: finish_reason == "length" -> truncation, 답 없음 -> parser_fail
3) 나머지 오답은 HF MMMU 데이터셋에서 문제/선택지/이미지를 id로 조인해 GPT(gpt-4o)에 보내 분류
4) Pydantic 기반 Structured Outputs를 사용하여 정확한 JSON 구조 강제
5) 결과를 jsonl로 저장(이어서 실행 가능), 집계 CSV와 사람 검수용 CSV 생성

설치:
  pip install openai datasets pillow pandas pydantic

실행 예:
  export OPENAI_API_KEY="sk-..."
  python classify_errors.py --log predictions.jsonl --out errors_classified.jsonl --limit 20
  python classify_errors.py --log predictions.jsonl --out errors_classified.jsonl --model gpt-4o
  python classify_errors.py --log predictions.jsonl --out errors_classified.jsonl --aggregate-only
"""
import argparse
import ast
import base64
import io
import json
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal, Optional

from pydantic import BaseModel, Field

PROMPT_VERSION = "v1"

CATEGORIES = [
    "perception", "reasoning", "calculation", "knowledge",
    "grading_mismatch", "question_issue", "other",
]
RULE_CATEGORIES = ["truncation", "parser_fail"]
VALID = set(CATEGORIES + RULE_CATEGORIES)

# ----------------------------------------------------------------------------
# Pydantic Structured Output 정의
# ----------------------------------------------------------------------------
CategoryLiteral = Literal[
    "perception", "reasoning", "calculation", "knowledge",
    "grading_mismatch", "question_issue", "other"
]

class ErrorClassification(BaseModel):
    category: CategoryLiteral = Field(..., description="The primary cause of the error.")
    evidence: str = Field(..., description="One sentence quoting or pointing to the specific part of the response.")
    first_error_step: str = Field(..., description="Where the response first goes wrong (short description).")
    second_guess: Optional[CategoryLiteral] = Field(None, description="Alternative category if uncertain, else null.")
    confidence: int = Field(..., ge=1, le=5, description="Confidence score from 1 to 5.")


GUIDE = """You are analyzing why a vision-language model (Qwen3-VL-4B-Instruct) answered
a college-level multimodal exam question (MMMU) incorrectly.

You will receive: the question, options (if any), one or more images, the ground-truth
answer, the model's parsed final answer, and the model's full response.
Classify the PRIMARY cause of the error.

Categories (choose exactly one):
- perception: The model misread the image (wrong value, symbol, label, axis, text,
  notation, or object), and this misreading led to the wrong answer.
- reasoning: The model read the information correctly but applied wrong logic,
  skipped a step, or drew a wrong conclusion.
- calculation: Reasoning is correct but an arithmetic/algebra/unit error produced the
  wrong result.
- knowledge: The model lacked or misapplied a domain fact, formula, theory, or
  convention needed to solve the problem.
- grading_mismatch: The model's final answer is actually equivalent to the ground truth
  but written differently (units, rounding, extra words, partial name), so it was
  marked wrong by string matching.
- question_issue: The ground truth looks wrong, or the question is ambiguous or
  unanswerable as given.
- other: None of the above fits. Explain in the evidence field.

Decision rules:
1. First check whether the model's final answer is equivalent to the ground truth. If so,
   choose grading_mismatch.
2. Then check whether the model's reading of the image is correct. If a misreading caused
   the error, choose perception, even if later steps are also wrong.
3. If the image reading is correct, check calculation, then reasoning, then knowledge.
4. Judge from what the response actually says. Do not assume a cause you cannot point to
   in the response.
5. If you are unsure between two categories, pick the more likely one and put the other
   in "second_guess"."""

LETTERS = "ABCDEFGHIJ"


# ----------------------------------------------------------------------------
# 유틸
# ----------------------------------------------------------------------------
def read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def subject_from_id(qid, fallback=None):
    m = re.match(r"^(?:validation|dev|test)_(.+)_\d+$", qid)
    return m.group(1) if m else fallback


def trunc_flags(resp):
    wait_count = len(re.findall(r"\bWait\b", resp))
    missing_opt = bool(re.search(
        r"not (?:among|an option|in the options|listed)|isn[’']t (?:among|an option)"
        r"|not one of the (?:options|choices)|not (?:matching|match) any",
        resp, re.I))
    return wait_count, missing_opt


def triage(item):
    if item.get("finish_reason") == "length":
        return "truncation"
    pred = item.get("prediction")
    if pred is None or str(pred).strip() == "":
        return "parser_fail"
    return "needs_llm"


def shorten(text, max_chars):
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n[... middle omitted ...]\n" + text[-half:]


class RateLimiter:
    def __init__(self, rpm):
        self.interval = 60.0 / rpm if rpm > 0 else 0
        self.lock = threading.Lock()
        self.next_time = 0.0

    def wait(self):
        if not self.interval:
            return
        with self.lock:
            now = time.time()
            delay = max(0.0, self.next_time - now)
            self.next_time = max(now, self.next_time) + self.interval
        if delay:
            time.sleep(delay)


# ----------------------------------------------------------------------------
# 데이터셋 조인 및 메시지 구성
# ----------------------------------------------------------------------------
def build_dataset_index(items, split):
    from datasets import load_dataset

    subjects = set()
    for it in items:
        s = subject_from_id(it["id"], it.get("subject"))
        if s:
            subjects.add(s)

    index = {}
    for subj in sorted(subjects):
        ds = load_dataset("MMMU/MMMU", subj, split=split)
        for i, qid in enumerate(ds["id"]):
            index[qid] = (ds, i)
    return index


def image_to_base64_url(img):
    img = img.convert("RGB")
    if max(img.size) > 1600:
        img.thumbnail((1600, 1600))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def build_messages(item, ds_row, max_chars):
    qtype = ds_row.get("question_type") or item.get("question_type", "")
    opts_raw = ds_row.get("options")
    options = []
    if opts_raw:
        options = ast.literal_eval(opts_raw) if isinstance(opts_raw, str) else list(opts_raw)

    gold = str(item.get("gold", ds_row.get("answer", "")))
    gold_text = gold
    if qtype == "multiple-choice" and gold in LETTERS[:len(options)]:
        gold_text = f"{gold} ({options[LETTERS.index(gold)]})"

    opt_block = "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(options)) if options else "(none, open-ended)"
    resp = shorten(str(item.get("prediction_raw", "")), max_chars)

    prompt_text = (
        f"[Subject] {item.get('subject', '')} / {item.get('subfield', '')}\n"
        f"[Question type] {qtype}\n"
        f"[Question]\n{ds_row['question']}\n"
        f"[Options]\n{opt_block}\n"
        f"[Ground truth] {gold_text}\n"
        f"[Model's parsed final answer] {item.get('prediction')}\n"
        f"[Model response]\n{resp}\n"
        f"[Images follow in order below]"
    )

    user_content = [{"type": "text", "text": prompt_text}]

    for i in range(1, 8):
        img = ds_row.get(f"image_{i}")
        if img is not None:
            user_content.append({"type": "text", "text": f"[image_{i}]"})
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_to_base64_url(img),
                    "detail": "high"
                }
            })

    return [
        {"role": "system", "content": GUIDE},
        {"role": "user", "content": user_content}
    ]


# ----------------------------------------------------------------------------
# OpenAI 호출
# ----------------------------------------------------------------------------
def call_openai(client, model, messages, limiter, max_retries=6):
    last_err = None
    for attempt in range(max_retries):
        try:
            limiter.wait()
            completion = client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=ErrorClassification,
                temperature=0,
            )
            parsed = completion.choices[0].message.parsed
            return parsed.model_dump()
        except Exception as e:
            last_err = e
            time.sleep(min(60, 2 ** attempt + random.random()))
    raise RuntimeError(f"failed after {max_retries} retries: {last_err}")


# ----------------------------------------------------------------------------
# 메인 처리
# ----------------------------------------------------------------------------
def base_record(item, model):
    return {
        "id": item["id"],
        "subject": item.get("subject"),
        "subfield": item.get("subfield"),
        "img_type": item.get("img_type"),
        "topic_difficulty": item.get("topic_difficulty"),
        "question_type": item.get("question_type"),
        "finish_reason": item.get("finish_reason"),
        "completion_tokens": item.get("completion_tokens"),
        "prompt_version": PROMPT_VERSION,
        "model": model,
    }


def load_done(out_path):
    done = {}
    if os.path.exists(out_path):
        for r in read_jsonl(out_path):
            done[r["id"]] = r
    return {k for k, v in done.items() if v.get("category") in VALID}


def run(args):
    items = read_jsonl(args.log)
    wrong = [it for it in items if not it.get("correct")]
    print(f"전체 {len(items)}개, 오답 {len(wrong)}개 ({len(wrong)/max(1,len(items)):.1%})")

    done = load_done(args.out)
    out_lock = threading.Lock()
    out_f = open(args.out, "a", encoding="utf-8")

    def write(rec):
        with out_lock:
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_f.flush()

    # 1) 규칙 분류
    needs_llm = []
    n_rule = 0
    for it in wrong:
        if it["id"] in done:
            continue
        label = triage(it)
        if label == "needs_llm":
            needs_llm.append(it)
            continue
        rec = base_record(it, "rule")
        rec.update({
            "category": label, "source": "rule", "evidence": "", "first_error_step": "",
            "second_guess": None, "confidence": 5
        })
        if label == "truncation":
            wc, mo = trunc_flags(str(it.get("prediction_raw", "")))
            rec["trunc_wait_count"] = wc
            rec["trunc_mentions_missing_option"] = mo
        write(rec)
        n_rule += 1
    print(f"규칙 분류 {n_rule}개 기록, LLM 대상 {len(needs_llm)}개")

    if args.limit:
        needs_llm = needs_llm[: args.limit]
        print(f"--limit {args.limit} 적용")

    # 2) LLM 분류 (OpenAI)
    if needs_llm:
        from openai import OpenAI
        client = OpenAI()  # OPENAI_API_KEY 환경변수 자동 참조
        limiter = RateLimiter(args.rpm)
        index = build_dataset_index(needs_llm, args.split)

        def work(it):
            qid = it["id"]
            if qid not in index:
                raise KeyError(f"{qid} not found in dataset")
            ds, i = index[qid]
            ds_row = ds[i]
            messages = build_messages(it, ds_row, args.max_resp_chars)
            res = call_openai(client, args.model, messages, limiter)
            rec = base_record(it, args.model)
            rec.update({
                "category": res.get("category"),
                "source": "llm",
                "evidence": res.get("evidence", ""),
                "first_error_step": res.get("first_error_step", ""),
                "second_guess": res.get("second_guess"),
                "confidence": res.get("confidence"),
            })
            return rec

        n_ok = n_fail = 0
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(work, it): it for it in needs_llm}
            for k, fut in enumerate(as_completed(futs), 1):
                it = futs[fut]
                try:
                    write(fut.result())
                    n_ok += 1
                except Exception as e:
                    rec = base_record(it, args.model)
                    rec.update({"category": "error", "source": "llm", "evidence": str(e)[:300]})
                    write(rec)
                    n_fail += 1
                if k % 10 == 0 or k == len(futs):
                    print(f"  진행 {k}/{len(futs)} (성공 {n_ok}, 실패 {n_fail})")
    out_f.close()


# ----------------------------------------------------------------------------
# 집계
# ----------------------------------------------------------------------------
def aggregate(args):
    import pandas as pd

    latest = {}
    for r in read_jsonl(args.out):
        latest[r["id"]] = r
    df = pd.DataFrame(latest.values())
    df = df[df["category"].isin(VALID)]
    if df.empty:
        print("집계할 데이터가 없습니다.")
        return

    outdir = os.path.splitext(args.out)[0] + "_summary"
    os.makedirs(outdir, exist_ok=True)

    overall = df["category"].value_counts()
    overall_pct = (overall / overall.sum() * 100).round(1)
    summary = pd.DataFrame({"count": overall, "percent": overall_pct})
    print("\n=== 전체 오답 유형 ===")
    print(summary)
    summary.to_csv(os.path.join(outdir, "overall.csv"))

    def to_list(v):
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v.startswith("["):
            try:
                return ast.literal_eval(v)
            except Exception:
                return [v]
        return [v]

    df_img = df.assign(img_type=df["img_type"].map(to_list)).explode("img_type")
    for col, frame in [("img_type", df_img), ("topic_difficulty", df),
                       ("question_type", df), ("subfield", df)]:
        ct = pd.crosstab(frame[col], frame["category"])
        ct["total"] = ct.sum(axis=1)
        ct_pct = pd.crosstab(frame[col], frame["category"], normalize="index").mul(100).round(1)
        ct.to_csv(os.path.join(outdir, f"by_{col}_count.csv"))
        ct_pct.to_csv(os.path.join(outdir, f"by_{col}_percent.csv"))
        if col in ("img_type", "topic_difficulty"):
            print(f"\n=== {col}별 오답 유형 (%) ===")
            print(ct_pct)

    tr = df[df["category"] == "truncation"]
    if "trunc_mentions_missing_option" in tr.columns and len(tr):
        rate = tr["trunc_mentions_missing_option"].fillna(False).mean() * 100
        print(f"\ntruncation 중 '선택지에 없다'고 언급한 비율: {rate:.1f}% ({len(tr)}개 중)")

    llm_df = df[df["source"] == "llm"]
    if len(llm_df):
        sample = llm_df.sample(n=min(args.review_n, len(llm_df)), random_state=0)
        cols = ["id", "subject", "category", "confidence", "second_guess",
                "evidence", "first_error_step"]
        sample = sample[cols].copy()
        sample["human_category"] = ""
        sample.to_csv(os.path.join(outdir, "human_review.csv"), index=False, encoding="utf-8-sig")
        low = llm_df[pd.to_numeric(llm_df["confidence"], errors="coerce") <= 2]
        print(f"\nLLM 분류 {len(llm_df)}개 중 confidence<=2: {len(low)}개 (우선 검수 권장)")
    print(f"\n결과 저장: {outdir}/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="예측 로그 jsonl")
    ap.add_argument("--out", default="errors_classified.jsonl")
    ap.add_argument("--split", default="validation")
    ap.add_argument("--model", default="gpt-4o", help="gpt-4o 권장 (또는 gpt-4o-mini)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rpm", type=int, default=60, help="분당 요청 수 상한 (Tier에 맞게 설정)")
    ap.add_argument("--max-resp-chars", type=int, default=8000)
    ap.add_argument("--limit", type=int, default=0, help="LLM 분류 개수 제한 (시험용)")
    ap.add_argument("--review-n", type=int, default=80)
    ap.add_argument("--aggregate-only", action="store_true")
    args = ap.parse_args()

    if not args.aggregate_only:
        run(args)
    aggregate(args)


if __name__ == "__main__":
    main()