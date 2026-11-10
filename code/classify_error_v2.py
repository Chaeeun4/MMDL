#!/usr/bin/env python3
"""
MMMU 오답 유형 분류 파이프라인 v2 (숭실대 API Gateway / OpenAI 호환)

v1 대비 변경점
- 직답(응답 <= N토큰)은 판단할 증거가 없으므로 LLM에 보내지 않고 'direct_answer'로 규칙 분류
- reasoning / perception은 하위 유형(subtype)까지 분류, knowledge는 부족한 개념(missing_concept)을 기록
- second_guess(차선 유형) 분석: 모호성 비율, 헷갈리는 유형 쌍(confusion pairs)
- 전체 분석 결과를 파일로 저장: report.md(읽기용), summary.json(기계용), 각종 CSV
- 실행 정보(모델, 프롬프트 버전, 입력 로그, 날짜)를 리포트에 기록

설치: pip install openai datasets pillow pandas pydantic
실행:
  export SSU_API_KEY="..." ; export SSU_MODEL="모델ID"
  python classify_errors_v2.py --log predictions.jsonl --out v2_test.jsonl --limit 3
  python classify_errors_v2.py --log predictions.jsonl --out errors_v2.jsonl
  python classify_errors_v2.py --log predictions.jsonl --out errors_v2.jsonl --aggregate-only

주의: v1 결과 파일(--out)에 이어 쓰지 말고 새 파일을 쓰세요 (스키마가 다릅니다).
"""
import argparse
import ast
import base64
import datetime
import io
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal, Optional

from pydantic import BaseModel, Field

PROMPT_VERSION = "v2"
DEFAULT_BASE_URL = "https://factchat-cloud.mindlogic.ai/v1/gateway"

CATEGORIES = [
    "perception", "reasoning", "calculation", "knowledge",
    "grading_mismatch", "question_issue", "other",
]
RULE_CATEGORIES = ["truncation", "parser_fail", "direct_answer"]
VALID = set(CATEGORIES + RULE_CATEGORIES)

SUBTYPES = {
    "reasoning": ["misread_condition", "wrong_method", "skipped_step", "option_mapping",
                  "logic_error", "late_revision", "other_reasoning"],
    "perception": ["text_ocr", "value_reading", "symbol_notation", "counting_spatial",
                   "object_recognition", "structure_relation", "other_perception"],
}

CategoryLiteral = Literal[
    "perception", "reasoning", "calculation", "knowledge",
    "grading_mismatch", "question_issue", "other",
]


class ErrorClassification(BaseModel):
    """LLM이 돌려준 JSON을 검증하는 스키마 (API에 강제하지 않고 사후 검증용)."""
    category: CategoryLiteral
    subtype: str = ""
    evidence: str = ""
    first_error_step: str = ""
    second_guess: Optional[CategoryLiteral] = None
    missing_concept: str = ""
    confidence: int = Field(..., ge=1, le=5)


GUIDE = """You are analyzing why a vision-language model (Qwen3-VL-4B-Instruct) answered
a college-level multimodal exam question (MMMU) incorrectly.

You will receive: the question, options (if any), one or more images, the ground-truth
answer, the model's parsed final answer, and the model's full response (its reasoning).
Classify the PRIMARY cause of the error, plus a subtype where applicable.

Categories (choose exactly one):
- perception: The model misread the image, and this misreading led to the wrong answer.
- reasoning: The model read the information correctly and had the needed knowledge, but its
  problem solving went wrong.
- calculation: Reasoning is correct but an arithmetic/algebra/unit error produced the wrong result.
- knowledge: The model lacked or misapplied a domain fact, formula, theory, or convention.
- grading_mismatch: The model's final answer is actually equivalent to the ground truth but
  written differently (units, rounding, extra words, partial name). Use ONLY if the response
  clearly shows the same answer; a bare answer with no reasoning is NOT grading_mismatch.
- question_issue: The ground truth looks wrong, or the question is ambiguous or unanswerable.
- other: None of the above fits. Explain in the evidence field.

Subtypes (required for perception and reasoning, otherwise use ""):
perception subtypes:
- text_ocr: misread printed/handwritten text or labels in the image
- value_reading: misread a number or value from a chart, table, axis, or scale
- symbol_notation: misread a symbol or notation (music notation, chemical structure, math symbols)
- counting_spatial: wrong count, position, orientation, or spatial arrangement
- object_recognition: misidentified an object, scene, or image type
- structure_relation: misread connections or relationships (graph edges, diagrams, flows)
- other_perception
reasoning subtypes:
- misread_condition: ignored or misinterpreted a condition, constraint, or what the question asks
- wrong_method: knew the relevant concepts but chose the wrong method, formula, or rule
- skipped_step: skipped or mishandled an intermediate step; incomplete chain of reasoning
- option_mapping: reached a plausible conclusion but mapped it to the wrong option, or misjudged option meaning
- logic_error: invalid inference or internal contradiction
- late_revision: had a correct answer or line of reasoning, then revised it into a wrong one
- other_reasoning

Decision rules:
1. First check whether the final answer is equivalent to the ground truth (grading_mismatch, with clear evidence).
2. Then check whether the model's reading of the image is correct. If a misreading caused the error, choose perception.
3. If the image reading is correct, check calculation, then reasoning vs knowledge: knowledge means the model lacked
   or misstated a needed fact; reasoning means it knew the facts but used them wrongly.
4. Judge ONLY from what the response actually shows. Do not assume a cause you cannot point to. If the response gives
   too little to judge, say so in evidence and use confidence 1 or 2.
5. If unsure between two categories, pick the more likely one and put the other in "second_guess".
6. For knowledge errors, put the missing concept in "missing_concept" as a short phrase (e.g. "contribution margin").

Output JSON only, with no extra text and no markdown code fences, in exactly this form:
{
  "category": "<one of: perception, reasoning, calculation, knowledge, grading_mismatch, question_issue, other>",
  "subtype": "<subtype for perception/reasoning, else empty string>",
  "evidence": "<one sentence quoting or pointing to the specific part of the response>",
  "first_error_step": "<where the response first goes wrong, short>",
  "second_guess": "<one of the categories, or null>",
  "missing_concept": "<short phrase for knowledge errors, else empty string>",
  "confidence": <integer 1-5>
}"""

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


def triage(item, direct_max):
    """규칙으로 판정 가능한 건 여기서 끝낸다. LLM이 필요하면 'needs_llm'."""
    if item.get("finish_reason") == "length":
        return "truncation"
    pred = item.get("prediction")
    if pred is None or str(pred).strip() == "":
        return "parser_fail"
    if (item.get("completion_tokens") or 0) <= direct_max:
        return "direct_answer"
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


class AbortRun(Exception):
    """재시도해도 소용없는 오류(인증, 잘못된 요청 등) 때문에 전체 실행을 멈출 때 사용."""


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
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


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
            user_content.append({"type": "image_url", "image_url": {"url": image_to_base64_url(img)}})

    return [{"role": "system", "content": GUIDE}, {"role": "user", "content": user_content}]


# ----------------------------------------------------------------------------
# LLM 호출 (OpenAI 호환 Chat Completions)
# ----------------------------------------------------------------------------
def parse_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        s, e = text.find("{"), text.rfind("}")
        if s == -1 or e <= s:
            raise
        obj = json.loads(text[s:e + 1])
    if isinstance(obj, list):
        obj = obj[0]
    return obj


def normalize(obj):
    """모델 출력의 사소한 형식 차이를 보정."""
    for k in ("second_guess",):
        v = obj.get(k)
        if isinstance(v, str) and v.strip().lower() in ("", "null", "none", "n/a"):
            obj[k] = None
    for k in ("subtype", "missing_concept", "evidence", "first_error_step"):
        if obj.get(k) is None:
            obj[k] = ""
    if "confidence" in obj:
        try:
            obj["confidence"] = int(round(float(obj["confidence"])))
        except (TypeError, ValueError):
            pass
    if isinstance(obj.get("category"), str):
        obj["category"] = obj["category"].strip().lower()
    if isinstance(obj.get("second_guess"), str):
        obj["second_guess"] = obj["second_guess"].strip().lower()
    if isinstance(obj.get("subtype"), str):
        obj["subtype"] = obj["subtype"].strip().lower()
    if obj.get("second_guess") == obj.get("category"):
        obj["second_guess"] = None
    return obj


def fix_subtype(res):
    cat, sub = res["category"], res.get("subtype", "")
    if cat in SUBTYPES:
        if sub not in SUBTYPES[cat]:
            res["subtype"] = "unspecified"
    else:
        res["subtype"] = ""
    return res


def call_llm(client, model, messages, limiter, use_temperature=True,
             reasoning_effort=None, max_retries=6):
    import openai

    non_retryable = (openai.BadRequestError, openai.AuthenticationError,
                     openai.PermissionDeniedError, openai.NotFoundError)
    kwargs = {"model": model, "messages": messages}
    if use_temperature:
        kwargs["temperature"] = 0
    if reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort

    last_err = None
    for attempt in range(max_retries):
        try:
            limiter.wait()
            completion = client.chat.completions.create(**kwargs)
            obj = normalize(parse_json(completion.choices[0].message.content))
            result = fix_subtype(ErrorClassification.model_validate(obj).model_dump())
            u = getattr(completion, "usage", None)
            if u is not None:
                details = getattr(u, "completion_tokens_details", None)
                result["usage"] = {
                    "prompt_tokens": getattr(u, "prompt_tokens", None),
                    "completion_tokens": getattr(u, "completion_tokens", None),
                    "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
                }
            return result
        except non_retryable as e:
            raise AbortRun(f"{type(e).__name__}: {e}") from e
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
    """현재 프롬프트 버전으로 유효하게 분류된 id 집합 (실패/다른 버전은 재시도)."""
    done = {}
    if os.path.exists(out_path):
        for r in read_jsonl(out_path):
            done[r["id"]] = r
    return {k for k, v in done.items()
            if v.get("category") in VALID and v.get("prompt_version") == PROMPT_VERSION}


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

    needs_llm, n_rule = [], 0
    for it in wrong:
        if it["id"] in done:
            continue
        label = triage(it, args.direct_max_tokens)
        if label == "needs_llm":
            needs_llm.append(it)
            continue
        rec = base_record(it, "rule")
        rec.update({"category": label, "subtype": "", "source": "rule", "evidence": "",
                    "first_error_step": "", "second_guess": None, "missing_concept": "",
                    "confidence": 5})
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

    if needs_llm:
        from openai import OpenAI

        api_key = os.environ.get("SSU_API_KEY")
        if not api_key:
            sys.exit("SSU_API_KEY 환경변수가 없습니다. export SSU_API_KEY=... 를 먼저 실행하세요.")
        client = OpenAI(base_url=os.environ.get("SSU_BASE_URL", DEFAULT_BASE_URL), api_key=api_key)
        limiter = RateLimiter(args.rpm)
        stop = threading.Event()
        abort_msg = []

        print("데이터셋 로딩 중 (처음에는 다운로드로 몇 분 걸릴 수 있음)...")
        index = build_dataset_index(needs_llm, args.split)

        def work(it):
            if stop.is_set():
                raise AbortRun("aborted")
            qid = it["id"]
            if qid not in index:
                raise KeyError(f"{qid} not found in dataset")
            ds, i = index[qid]
            messages = build_messages(it, ds[i], args.max_resp_chars)
            res = call_llm(client, args.model, messages, limiter,
                           use_temperature=not args.no_temperature,
                           reasoning_effort=args.reasoning_effort)
            rec = base_record(it, args.model)
            rec.update({
                "usage": res.get("usage"),
                "category": res["category"],
                "subtype": res.get("subtype", ""),
                "source": "llm",
                "evidence": res.get("evidence", ""),
                "first_error_step": res.get("first_error_step", ""),
                "second_guess": res.get("second_guess"),
                "missing_concept": res.get("missing_concept", ""),
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
                except AbortRun as e:
                    if str(e) != "aborted" and not abort_msg:
                        abort_msg.append(str(e))
                        stop.set()
                except Exception as e:
                    rec = base_record(it, args.model)
                    rec.update({"category": "error", "source": "llm", "evidence": str(e)[:300]})
                    write(rec)
                    n_fail += 1
                if k % 10 == 0 or k == len(futs):
                    print(f"  진행 {k}/{len(futs)} (성공 {n_ok}, 실패 {n_fail})")
        if abort_msg:
            print("\n[중단] 재시도해도 해결되지 않는 오류:")
            print("  " + abort_msg[0])
            print("  - 401: 키 확인 / 400, 404: 모델 ID, 이미지 지원, temperature 지원 확인")
            print("  - 오류에 temperature가 나오면 --no-temperature 를 추가하세요.")
    out_f.close()


# ----------------------------------------------------------------------------
# 집계 + 리포트
# ----------------------------------------------------------------------------
def md_table(df, index=True):
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.values) + " |")
    return "\n".join(lines)


def to_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.startswith("["):
        try:
            return ast.literal_eval(v)
        except Exception:
            return [v]
    return [v]


def aggregate(args):
    import numpy as np
    import pandas as pd

    if not os.path.exists(args.out):
        print("결과 파일이 없습니다.")
        return

    latest = {}
    for r in read_jsonl(args.out):
        latest[r["id"]] = r
    df = pd.DataFrame(latest.values())
    df = df[df["category"].isin(VALID)].copy()
    if df.empty:
        print("집계할 데이터가 없습니다.")
        return

    total_q, acc = None, None
    if args.log and os.path.exists(args.log):
        log_items = read_jsonl(args.log)
        total_q = len(log_items)
        acc = sum(1 for x in log_items if x.get("correct")) / max(1, total_q)

    df["completion_tokens"] = pd.to_numeric(df["completion_tokens"], errors="coerce").fillna(0)
    df["resp_type"] = np.where(df["finish_reason"] == "length", "truncated",
                               np.where(df["completion_tokens"] <= args.direct_max_tokens, "direct", "cot"))
    n_err = len(df)

    outdir = os.path.splitext(args.out)[0] + "_summary"
    os.makedirs(outdir, exist_ok=True)
    save = lambda t, name, idx=True: t.to_csv(os.path.join(outdir, name), index=idx, encoding="utf-8-sig")

    summary = {"meta": {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "log": args.log, "out": args.out, "prompt_version": PROMPT_VERSION,
        "models": sorted(set(df.get("model", pd.Series(dtype=str)).dropna().astype(str))),
        "direct_max_tokens": args.direct_max_tokens,
        "total_questions": total_q, "accuracy": acc, "n_errors": n_err}}
    md = []
    md.append("# MMMU 오답 분석 리포트\n")
    md.append("## 1. 실행 정보\n")
    md.append(f"- 생성 시각: {summary['meta']['generated_at']}")
    md.append(f"- 입력 로그: `{args.log}` / 분류 결과: `{args.out}`")
    md.append(f"- 분류 모델: {', '.join(summary['meta']['models'])} / 프롬프트 버전: {PROMPT_VERSION}")
    if total_q:
        md.append(f"- 전체 {total_q}문제, 정확도 {acc:.2%}, 오답 {n_err}개")
    md.append(f"- 직답 기준: 응답 {args.direct_max_tokens}토큰 이하 (판단할 증거가 없어 LLM 분류에서 제외, direct_answer)\n")

    # 전체 유형
    ov = df["category"].value_counts().rename("count").to_frame()
    ov["percent_of_errors"] = (ov["count"] / n_err * 100).round(1)
    if total_q:
        ov["pct_of_all_questions"] = (ov["count"] / total_q * 100).round(2)
    print("\n=== 전체 오답 유형 ===")
    print(ov)
    save(ov, "overall.csv")
    summary["overall"] = ov.to_dict(orient="index")
    md.append("## 2. 오답 유형 (pct_of_all_questions = 정확도에 환산했을 때의 %p)\n")
    md.append(md_table(ov) + "\n")

    # 응답 유형 x 카테고리
    ct = pd.crosstab(df["category"], df["resp_type"], margins=True)
    save(ct, "category_by_resp_type.csv")
    summary["category_by_resp_type"] = ct.to_dict()
    md.append("## 3. 응답 유형별 (direct=직답 / cot=풀이 있음 / truncated=잘림)\n")
    md.append(md_table(ct) + "\n")

    # 하위 유형
    llm = df[df["source"] == "llm"].copy()
    md.append("## 4. 하위 유형 (LLM 분류분만)\n")
    for cat in SUBTYPES:
        sub = llm[llm["category"] == cat]
        if len(sub):
            t = sub["subtype"].fillna("").replace("", "(none)").value_counts().rename("count").to_frame()
            t["percent"] = (t["count"] / len(sub) * 100).round(1)
            print(f"\n=== {cat} 하위 유형 ===")
            print(t)
            save(t, f"subtype_{cat}.csv")
            summary[f"subtype_{cat}"] = t.to_dict(orient="index")
            md.append(f"### {cat} ({len(sub)}개)\n")
            md.append(md_table(t) + "\n")

    # knowledge 개념
    kn = llm[llm["category"] == "knowledge"]
    if len(kn) and "missing_concept" in kn:
        concepts = kn["missing_concept"].fillna("").str.lower().str.strip()
        concepts = concepts[concepts != ""]
        if len(concepts):
            t = concepts.value_counts().head(15).rename("count").to_frame()
            top10 = concepts.value_counts().head(10).sum() / len(concepts) * 100
            save(t, "knowledge_concepts.csv")
            summary["knowledge_concepts_top"] = t.to_dict(orient="index")
            md.append("### knowledge: 부족한 개념 상위 (개념이 몰려 있으면 구체적 갭, 흩어져 있으면 전반적 갭)\n")
            md.append(f"상위 10개 개념이 차지하는 비율: {top10:.1f}% (개념 {len(concepts)}개 중)\n")
            md.append(md_table(t) + "\n")

    # second_guess / 모호성
    md.append("## 5. 모호성 분석 (second_guess, confidence)\n")
    if len(llm):
        conf = pd.to_numeric(llm["confidence"], errors="coerce")
        has_sg = (llm["second_guess"].notna() & (llm["second_guess"].astype(str) != "None")
                  & (llm["second_guess"] != llm["category"]))
        amb = has_sg | (conf <= 2)
        md.append(f"- LLM 분류 {len(llm)}개 중 차선 유형이 있는 것: {int(has_sg.sum())}개 ({has_sg.mean():.1%}), "
                  f"confidence<=2: {int((conf <= 2).sum())}개, 둘 중 하나라도 해당: {int(amb.sum())}개 ({amb.mean():.1%})")
        summary["ambiguity"] = {"with_second_guess": int(has_sg.sum()), "low_conf": int((conf <= 2).sum()),
                                "either": int(amb.sum()), "n_llm": len(llm)}
        pairs = pd.crosstab(llm.loc[has_sg, "category"], llm.loc[has_sg, "second_guess"])
        if pairs.size:
            save(pairs, "ambiguity_pairs_matrix.csv")
            flat = pairs.stack().rename("count").reset_index()
            flat = flat[flat["count"] > 0].sort_values("count", ascending=False)
            flat.columns = ["primary", "second_guess", "count"]
            save(flat, "ambiguity_pairs.csv", idx=False)
            summary["ambiguity_pairs"] = flat.head(10).to_dict(orient="records")
            print("\n=== 헷갈리는 유형 쌍 (primary -> second_guess) ===")
            print(flat.head(10).to_string(index=False))
            md.append("- 많이 헷갈리는 쌍은 카테고리 정의가 모호하다는 신호입니다. 정의를 고치거나 한 칸으로 합쳐 보세요.\n")
            md.append(md_table(flat.head(10), index=False) + "\n")
        md.append("- 보고서의 주 집계는 primary 하나를 쓰고, second_guess는 모호성 지표와 검수 대상 선정에만 씁니다.\n")
    else:
        md.append("- LLM 분류가 없습니다.\n")

    # 차원별
    md.append("## 6. 유형별 오답 구성 (n이 작은 행(*)은 해석 주의)\n")
    df_img = df.assign(img_type=df["img_type"].map(to_list)).explode("img_type").reset_index(drop=True)  # explode 후 중복 인덱스 제거 (crosstab 오류 방지)
    for col, frame in [("img_type", df_img), ("topic_difficulty", df), ("question_type", df), ("subfield", df)]:
        c = pd.crosstab(frame[col], frame["category"])
        c["total"] = c.sum(axis=1)
        pct = pd.crosstab(frame[col], frame["category"], normalize="index").mul(100).round(1)
        save(c, f"by_{col}_count.csv")
        save(pct, f"by_{col}_percent.csv")
        if col in ("img_type", "topic_difficulty"):
            print(f"\n=== {col}별 오답 유형 (%) ===")
            print(pct)
            show = pct.copy()
            show.index = [f"{i}{'*' if c.loc[i, 'total'] < 10 else ''} (n={c.loc[i, 'total']})" for i in show.index]
            md.append(f"### {col}\n")
            md.append(md_table(show) + "\n")

    # truncation
    tr = df[df["category"] == "truncation"]
    if len(tr) and "trunc_mentions_missing_option" in tr.columns:
        rate = pd.to_numeric(tr["trunc_mentions_missing_option"], errors="coerce").mean() * 100
        print(f"\ntruncation 중 '선택지에 없다'고 언급한 비율: {rate:.1f}% ({len(tr)}개 중)")
        md.append("## 7. 잘림(truncation)\n")
        md.append(f"- {len(tr)}개 중 '계산 결과가 선택지에 없다'고 언급하며 루프에 빠진 비율: {rate:.1f}%\n")
        summary["truncation"] = {"n": len(tr), "mentions_missing_option_pct": round(float(rate), 1)}

    # 토큰
    if "usage" in df.columns:
        us = [x for x in df["usage"] if isinstance(x, dict)]
        if us:
            tot = lambda k: sum((x.get(k) or 0) for x in us)
            n = len(us)
            md.append("## 8. 분류 비용(토큰)\n")
            md.append(f"- LLM {n}건: 입력 {tot('prompt_tokens'):,} / 출력 {tot('completion_tokens'):,} "
                      f"(reasoning {tot('reasoning_tokens'):,}), 건당 평균 입력 {tot('prompt_tokens')//n:,} / 출력 {tot('completion_tokens')//n:,}\n")
            summary["tokens"] = {"n": n, "prompt": tot("prompt_tokens"), "completion": tot("completion_tokens"),
                                 "reasoning": tot("reasoning_tokens")}

    # 검수 샘플: 모호한 것 우선 + 무작위
    if len(llm):
        conf = pd.to_numeric(llm["confidence"], errors="coerce")
        has_sg = (llm["second_guess"].notna() & (llm["second_guess"].astype(str) != "None")
                  & (llm["second_guess"] != llm["category"]))
        amb_df = llm[has_sg | (conf <= 2)]
        n_amb = min(len(amb_df), args.review_n // 2)
        picked = amb_df.sample(n=n_amb, random_state=0) if n_amb else amb_df.iloc[0:0]
        rest = llm.drop(picked.index)
        picked = pd.concat([picked, rest.sample(n=min(args.review_n - len(picked), len(rest)), random_state=0)])
        cols = ["id", "subject", "category", "subtype", "confidence", "second_guess", "evidence", "first_error_step"]
        sample = picked[cols].copy()
        sample["human_category"] = ""
        save(sample, "human_review.csv", idx=False)
        md.append("## 9. 사람 검수\n")
        md.append(f"- `human_review.csv`: {len(sample)}개 (모호한 문항 {n_amb}개 + 무작위). "
                  "검수 후 LLM 분류와의 일치율, 교차표를 이 리포트에 추가하세요.\n")

    with open(os.path.join(outdir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2,
                  default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(f"\n결과 저장: {outdir}/  (report.md, summary.json, 각종 CSV)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="예측 로그 jsonl")
    ap.add_argument("--out", default="errors_v2.jsonl")
    ap.add_argument("--split", default="validation")
    ap.add_argument("--model", default=os.environ.get("SSU_MODEL"),
                    help="이미지를 지원하는 모델 ID (기본값: 환경변수 SSU_MODEL)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rpm", type=int, default=60, help="분당 요청 수 상한 (게이트웨이 한도: 60초에 120건)")
    ap.add_argument("--max-resp-chars", type=int, default=8000)
    ap.add_argument("--direct-max-tokens", type=int, default=20,
                    help="이 토큰 수 이하의 응답은 직답으로 보고 LLM 분류에서 제외")
    ap.add_argument("--limit", type=int, default=0, help="LLM 분류 개수 제한 (시험용)")
    ap.add_argument("--review-n", type=int, default=80)
    ap.add_argument("--no-temperature", action="store_true")
    ap.add_argument("--reasoning-effort", default=None,
                    choices=["none", "minimal", "low", "medium", "high"])
    ap.add_argument("--aggregate-only", action="store_true")
    args = ap.parse_args()

    if not args.aggregate_only:
        if not args.model:
            ap.error("모델 ID가 필요합니다: --model 모델ID 또는 export SSU_MODEL=모델ID")
        run(args)
    aggregate(args)


if __name__ == "__main__":
    main()