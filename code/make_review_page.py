#!/usr/bin/env python3
"""
human_review.csv의 각 행(id)에 대해 문제, 선택지, 이미지, 정답, 모델 응답을 한 페이지(HTML)로 모아 준다.
브라우저로 열어 읽으면서 human_review.csv의 human_category 칸을 채우면 된다.
기본은 LLM 분류를 숨긴 '블라인드' 모드(쏠림 방지). 비교할 때만 --show-llm.

설치: pip install datasets pillow
실행:
  python make_review_page.py --review human_review.csv --log predictions.jsonl --out review.html
  python make_review_page.py --review human_review.csv --log predictions.jsonl --out review_llm.html --show-llm
"""
import argparse
import ast
import base64
import csv
import html
import io
import json
import re

LETTERS = "ABCDEFGHIJ"

GUIDE_HTML = """
<div class="guide">
<b>판단 순서</b> (human_category에 아래 영어 라벨을 적으세요)<br>
1. 모델의 최종 답이 사실 정답과 같은 뜻인데 표기만 달라서 틀렸나? → <code>grading_mismatch</code><br>
2. 모델이 이미지를 잘못 읽었나(값, 기호, 글자, 개수, 구조)? → <code>perception</code><br>
3. 이미지는 맞게 읽었는데 개념, 공식, 사실을 모르거나 틀렸나? → <code>knowledge</code><br>
4. 개념은 아는데 논리 전개, 조건 해석, 선택지 연결이 틀렸나? → <code>reasoning</code> (산술 실수면 <code>calculation</code>)<br>
5. 정답이 이상하거나 문제가 모호한가? → <code>question_issue</code> / 어디에도 안 맞으면 <code>other</code><br>
<i>팁: 모델이 처음으로 틀린 지점을 응답에서 찾고, 그 원인이 무엇인지 보세요.</i>
</div>
"""

CSS = """
body{font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:900px;margin:20px auto;padding:0 12px;color:#222}
.card{border:1px solid #ccc;border-radius:8px;padding:14px;margin:18px 0}
.head{font-size:13px;color:#555;margin-bottom:6px}
.q{white-space:pre-wrap;font-size:15px;margin:8px 0}
.opts{margin:6px 0 6px 12px}
.opts div.gold{background:#d8f5d0;font-weight:bold}
img{max-width:100%;border:1px solid #ddd;margin:4px 0}
.ans{margin:8px 0;padding:6px 8px;background:#fff3cd;border-radius:4px}
pre{white-space:pre-wrap;background:#f6f6f6;padding:8px;max-height:420px;overflow:auto;font-size:12.5px}
.llm{background:#e8f0fe;padding:6px 8px;border-radius:4px;margin-top:8px;font-size:13px}
.guide{background:#f0f7ff;border:1px solid #bcd;padding:10px;border-radius:6px;font-size:14px;line-height:1.6}
code{background:#eee;padding:1px 4px;border-radius:3px}
"""


def subject_from_id(qid, fallback=None):
    m = re.match(r"^(?:validation|dev|test)_(.+)_\d+$", qid)
    return m.group(1) if m else fallback


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def img_to_data_uri(img, max_side=1100):
    img = img.convert("RGB")
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def shorten(text, n):
    if len(text) <= n:
        return text
    h = n // 2
    return text[:h] + "\n\n[... 중간 생략 ...]\n\n" + text[-h:]


def render_card(num, total, row, item, ds_row, show_llm, max_chars):
    e = html.escape
    qtype = ds_row.get("question_type") or item.get("question_type", "")
    opts_raw = ds_row.get("options")
    options = []
    if opts_raw:
        options = ast.literal_eval(opts_raw) if isinstance(opts_raw, str) else list(opts_raw)
    gold = str(item.get("gold", ds_row.get("answer", "")))
    pred = item.get("prediction")

    parts = [f'<div class="card" id="{e(row["id"])}">']
    parts.append(
        f'<div class="head">#{num}/{total} &nbsp; <b>{e(row["id"])}</b> &nbsp; '
        f'{e(str(item.get("subfield", "")))} &nbsp; {e(str(item.get("img_type", "")))} '
        f'&nbsp; {e(str(qtype))} &nbsp; finish: {e(str(item.get("finish_reason", "")))} '
        f'&nbsp; tokens: {e(str(item.get("completion_tokens", "")))}</div>'
    )
    parts.append(f'<div class="q">{e(str(ds_row.get("question", "")))}</div>')
    for i in range(1, 8):
        img = ds_row.get(f"image_{i}")
        if img is not None:
            parts.append(f'<div>[image_{i}]<br><img src="{img_to_data_uri(img)}"></div>')
    if options:
        parts.append('<div class="opts">')
        for i, o in enumerate(options):
            cls = ' class="gold"' if LETTERS[i] == gold else ""
            parts.append(f"<div{cls}>{LETTERS[i]}. {e(str(o))}</div>")
        parts.append("</div>")
    parts.append(
        f'<div class="ans"><b>정답:</b> {e(gold)} &nbsp;&nbsp; <b>모델 최종 답(파서 추출):</b> {e(str(pred))}</div>'
    )
    expl = str(ds_row.get("explanation") or "").strip()
    if expl:
        parts.append(f'<div class="ans"><b>데이터셋 해설:</b> {e(expl)}</div>')
    parts.append("<b>모델 응답</b>")
    parts.append(f"<pre>{e(shorten(str(item.get('prediction_raw', '')), max_chars))}</pre>")
    if show_llm:
        parts.append(
            f'<div class="llm"><b>LLM 분류:</b> {e(row.get("category", ""))} '
            f'(conf {e(row.get("confidence", ""))}, 차선 {e(row.get("second_guess", ""))})<br>'
            f'근거: {e(row.get("evidence", ""))}<br>첫 오류: {e(row.get("first_error_step", ""))}</div>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def build_html(rows, items, ds_lookup, show_llm, max_chars):
    cards = []
    for n, row in enumerate(rows, 1):
        qid = row["id"]
        if qid not in items or qid not in ds_lookup:
            cards.append(f'<div class="card"><b>{html.escape(qid)}</b>: 로그나 데이터셋에서 찾지 못했습니다.</div>')
            continue
        cards.append(render_card(n, len(rows), row, items[qid], ds_lookup[qid](), show_llm, max_chars))
    mode = "LLM 분류 표시" if show_llm else "블라인드(LLM 분류 숨김)"
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>MMMU 오답 검수</title>"
            f"<style>{CSS}</style></head><body><h2>MMMU 오답 검수 ({mode})</h2>{GUIDE_HTML}"
            + "\n".join(cards) + "</body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", required=True, help="human_review.csv")
    ap.add_argument("--log", required=True, help="예측 로그 jsonl")
    ap.add_argument("--out", default="review.html")
    ap.add_argument("--split", default="validation")
    ap.add_argument("--max-resp-chars", type=int, default=4000)
    ap.add_argument("--show-llm", action="store_true", help="LLM 분류를 함께 표시")
    args = ap.parse_args()

    with open(args.review, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    items = {r["id"]: r for r in read_jsonl(args.log)}

    from datasets import load_dataset
    subjects = sorted({subject_from_id(r["id"], r.get("subject")) for r in rows})
    ds_lookup = {}
    for subj in subjects:
        ds = load_dataset("MMMU/MMMU", subj, split=args.split)
        for i, qid in enumerate(ds["id"]):
            ds_lookup[qid] = (lambda ds=ds, i=i: ds[i])  # 필요할 때만 이미지 디코딩

    page = build_html(rows, items, ds_lookup, args.show_llm, args.max_resp_chars)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"{len(rows)}개 문항 -> {args.out} (브라우저로 열어서 읽으세요)")


if __name__ == "__main__":
    main()