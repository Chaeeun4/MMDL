#!/usr/bin/env python3
"""
MMMU 오답 유형 분류 파이프라인 (숭실대 API Gateway / OpenAI 호환 버전)

1) 로그(jsonl)에서 오답만 추림
2) 규칙으로 먼저 분류: finish_reason == "length" -> truncation, 답 없음 -> parser_fail
3) 나머지 오답은 HF MMMU 데이터셋에서 문제/선택지/이미지를 id로 조인해 LLM에 보내 분류
4) 응답은 JSON 텍스트로 받아 Pydantic으로 검증 (Structured Outputs 기능에 의존하지 않음)
5) 결과를 jsonl로 저장(이어서 실행 가능), 집계 CSV와 사람 검수용 CSV 생성

설치:
  pip install openai datasets pillow pandas pydantic

실행 예 (키와 모델 ID는 환경변수로, 코드/GitHub에 절대 넣지 말 것):
  export SSU_API_KEY="발급받은키"
  export SSU_MODEL="페이지에서 복사한 이미지 지원 모델 ID"
  python classify_errors_ssu.py --log predictions.jsonl --out test.jsonl --limit 3
  python classify_errors_ssu.py --log predictions.jsonl --out errors_classified.jsonl
  python classify_errors_ssu.py --log predictions.jsonl --out errors_classified.jsonl --aggregate-only
"""
import argparse
import ast
import base64
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

PROMPT_VERSION = "v1"
DEFAULT_BASE_URL = "https://factchat-cloud.mindlogic.ai/v1/gateway"

CATEGORIES = [
    "perception", "reasoning", "calculation", "knowledge",
    "grading_mismatch", "question_issue", "other",
]
RULE_CATEGORIES = ["truncation", "parser_fail"]
VALID = set(CATEGORIES + RULE_CATEGORIES)

CategoryLiteral = Literal[
    "perception", "reasoning", "calculation", "knowledge",
    "grading_mismatch", "question_issue", "other",
]


class ErrorClassification(BaseModel):
    """LLM이 돌려준 JSON을 검증하기 위한 스키마 (API에 강제하지 않고 사후 검증용)."""
    category: CategoryLiteral = Field(..., description="The primary cause of the error.")
    evidence: str = Field("", description="One sentence pointing to the specific part of the response.")
    first_error_step: str = Field("", description="Where the response first goes wrong (short).")
    second_guess: Optional[CategoryLiteral] = Field(None, description="Alternative category, else null.")
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
   in "second_guess".

Output JSON only, with no extra text and no markdown code fences, in exactly this form:
{
  "category": "<one of: perception, reasoning, calculation, knowledge, grading_mismatch, question_issue, other>",
  "evidence": "<one sentence quoting or pointing to the specific part of the response>",
  "first_error_step": "<where the response first goes wrong, short>",
  "second_guess": "<one of the categories, or null>",
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


def triage(item):
    """규칙으로 판정 가능한 건 여기서 끝낸다. LLM이 필요하면 'needs_llm'."""
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


class AbortRun(Exception):
    """재시도해도 소용없는 오류(인증, 잘못된 요청 등) 때문에 전체 실행을 멈출 때 사용."""


# ----------------------------------------------------------------------------
# 데이터셋 조인 및 메시지 구성
# ----------------------------------------------------------------------------
def build_dataset_index(items, split):
    """필요한 과목만 로드. ds["id"]는 이미지를 디코딩하지 않아 메모리를 아낀다."""
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
            # "detail" 옵션은 OpenAI 전용이라 게이트웨이의 다른 모델에서 오류가 날 수 있어 뺐다.
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_to_base64_url(img)},
            })

    return [
        {"role": "system", "content": GUIDE},
        {"role": "user", "content": user_content},
    ]


# ----------------------------------------------------------------------------
# LLM 호출 (OpenAI 호환 Chat Completions)
# ----------------------------------------------------------------------------
def parse_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # 앞뒤에 잡설이 붙은 경우: 첫 '{'부터 마지막 '}'까지만 시도
        s, e = text.find("{"), text.rfind("}")
        if s == -1 or e <= s:
            raise
        obj = json.loads(text[s:e + 1])
    if isinstance(obj, list):
        obj = obj[0]
    return obj


def normalize(obj):
    """모델 출력의 사소한 형식 차이(문자열 'null', 소수 confidence 등)를 보정."""
    sg = obj.get("second_guess")
    if isinstance(sg, str) and sg.strip().lower() in ("", "null", "none", "n/a"):
        obj["second_guess"] = None
    if "confidence" in obj:
        try:
            obj["confidence"] = int(round(float(obj["confidence"])))
        except (TypeError, ValueError):
            pass
    if isinstance(obj.get("category"), str):
        obj["category"] = obj["category"].strip().lower()
    return obj


def call_llm(client, model, messages, limiter, use_temperature=True,
             reasoning_effort=None, max_retries=6):
    import openai

    non_retryable = (
        openai.BadRequestError,
        openai.AuthenticationError,
        openai.PermissionDeniedError,
        openai.NotFoundError,
    )
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
            result = ErrorClassification.model_validate(obj).model_dump()
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
            # 몇 번을 다시 해도 같은 결과: 원인을 바로 보여 주고 전체 실행을 멈춘다.
            raise AbortRun(f"{type(e).__name__}: {e}") from e
        except Exception as e:  # 429, 5xx, 연결 오류, JSON 파싱/검증 실패
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
    """이미 유효하게 분류된 id 집합 (실패/invalid는 다음 실행에서 재시도)."""
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
            "second_guess": None, "confidence": 5,
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

    # 2) LLM 분류
    if needs_llm:
        from openai import OpenAI

        api_key = os.environ.get("SSU_API_KEY")
        if not api_key:
            sys.exit("SSU_API_KEY 환경변수가 없습니다. export SSU_API_KEY=... 를 먼저 실행하세요.")
        client = OpenAI(
            base_url=os.environ.get("SSU_BASE_URL", DEFAULT_BASE_URL),
            api_key=api_key,
        )
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
            ds_row = ds[i]
            messages = build_messages(it, ds_row, args.max_resp_chars)
            res = call_llm(client, args.model, messages, limiter,
                           use_temperature=not args.no_temperature,
                           reasoning_effort=args.reasoning_effort)
            rec = base_record(it, args.model)
            rec.update({
                "usage": res.get("usage"),
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
                except AbortRun as e:
                    # 중단 사유는 한 번만 출력하고, 실패 기록은 남기지 않아 다음 실행에서 재시도된다.
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
            print("\n[중단] 재시도해도 해결되지 않는 오류가 발생했습니다:")
            print("  " + abort_msg[0])
            print("  - 401: 키 확인 / 400 또는 404: 모델 ID, 이미지 지원 여부, temperature 지원 여부 확인")
            print("  - 오류에 temperature가 언급되면 --no-temperature 옵션을 추가하세요.")
    out_f.close()


# ----------------------------------------------------------------------------
# 집계
# ----------------------------------------------------------------------------
def aggregate(args):
    import pandas as pd

    if not os.path.exists(args.out):
        print("결과 파일이 없습니다.")
        return
    latest = {}
    for r in read_jsonl(args.out):
        latest[r["id"]] = r  # 같은 id는 마지막 기록만 사용
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

    if "usage" in df.columns:
        us = [x for x in df["usage"] if isinstance(x, dict)]
        if us:
            def tot(k):
                return sum((x.get(k) or 0) for x in us)
            n = len(us)
            print(f"\n토큰 사용량 (LLM {n}건): 입력 {tot('prompt_tokens'):,} / "
                  f"출력 {tot('completion_tokens'):,} (이 중 reasoning {tot('reasoning_tokens'):,})")
            print(f"  건당 평균: 입력 {tot('prompt_tokens') // n:,} / 출력 {tot('completion_tokens') // n:,}")

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
    ap.add_argument("--model", default=os.environ.get("SSU_MODEL"),
                    help="이미지를 지원하는 모델 ID (기본값: 환경변수 SSU_MODEL)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rpm", type=int, default=60, help="분당 요청 수 상한 (게이트웨이 한도: 60초에 120건)")
    ap.add_argument("--max-resp-chars", type=int, default=8000)
    ap.add_argument("--limit", type=int, default=0, help="LLM 분류 개수 제한 (시험용)")
    ap.add_argument("--review-n", type=int, default=80)
    ap.add_argument("--no-temperature", action="store_true",
                    help="모델이 temperature 파라미터를 거부할 때 사용")
    ap.add_argument("--reasoning-effort", default=None,
                    choices=["none", "minimal", "low", "medium", "high"],
                    help="추론 계열 모델(GPT-5.x 등)의 reasoning 양. 낮출수록 토큰이 줄어듦 "
                         "(Gateway/모델이 지원하지 않으면 400 오류가 나며, 그때는 이 옵션을 빼세요)")
    ap.add_argument("--aggregate-only", action="store_true")
    args = ap.parse_args()

    if not args.aggregate_only:
        if not args.model:
            ap.error("모델 ID가 필요합니다: --model 모델ID 또는 export SSU_MODEL=모델ID")
        run(args)
    aggregate(args)


if __name__ == "__main__":
    main()