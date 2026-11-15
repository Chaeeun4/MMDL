"""
Teacher distillation data: an external API model (allowed for training-data
generation, never at eval) answers ViRL39K questions (MMMU overlap removed),
mainly the ones the 4B model could not solve cleanly. Output rows use the
gen.jsonl format of code/gen_rft.py, so the same `select` step filters them
(correct vs gold, <=1500 student tokens, ends with 'Answer:', no loops) and
mixes them with the 4B model's own samples:

    export OPENAI_API_KEY=...            # or ANTHROPIC_API_KEY with --provider anthropic
    python code/gen_teacher.py --ids_file /data/$USER/rft/c1/no_clean_ids.txt \
        --model gpt-4.1 --out /data/$USER/rft/c2/teacher.jsonl
    python code/gen_rft.py select --gen /data/$USER/rft/c1/gen.jsonl /data/$USER/rft/c2/teacher.jsonl \
        --out_dir /data/$USER/rft/c2 --pick random --exclude_agents concise

--base_url points the OpenAI client at any OpenAI-compatible endpoint
(Gemini, OpenRouter, DashScope, a local vLLM server). No GPU is used.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_rft import AGENTS, MODEL_NAME, MODEL_REVISION, final_answer, is_correct, load_pool  # noqa: E402

# Same describe-then-solve style the student is trained with, plus a length hint
# so most traces fit the 1500-token selection cap.
TEACHER_HINT = " Keep the reasoning complete but compact (well under 1000 words)."


def encode_image(path: str, max_px: int) -> tuple[str, str]:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width * im.height > max_px:
        s = (max_px / (im.width * im.height)) ** 0.5
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return "image/png", base64.b64encode(buf.getvalue()).decode()


def build_parts(q, max_px):
    """Interleaved text/image parts in question order; images not referenced go first."""
    instr = AGENTS["describe"]["mc" if q["is_mc"] else "open"] + TEACHER_HINT
    parts, cur, used = [], 0, set()
    for m in re.finditer(r"<image (\d+)>", q["question"]):
        if m.start() > cur:
            parts.append(("text", q["question"][cur:m.start()]))
        i = int(m.group(1))
        parts.append(("image", q["images"][i - 1]))
        used.add(i)
        cur = m.end()
    parts.append(("text", q["question"][cur:] + "\n\n" + instr))
    extra = [("image", p) for i, p in enumerate(q["images"], 1) if i not in used]
    return [(k, encode_image(v, max_px) if k == "image" else v) for k, v in extra + parts]


def call_openai(client, model, parts, max_tokens):
    content = [{"type": "text", "text": v} if k == "text" else
               {"type": "image_url", "image_url": {"url": f"data:{v[0]};base64,{v[1]}"}} for k, v in parts]
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": content}],
                                       max_completion_tokens=max_tokens, temperature=0.7)
    c = r.choices[0]
    return c.message.content or "", "stop" if c.finish_reason == "stop" else "length"


def call_anthropic(client, model, parts, max_tokens):
    content = [{"type": "text", "text": v} if k == "text" else
               {"type": "image", "source": {"type": "base64", "media_type": v[0], "data": v[1]}} for k, v in parts]
    r = client.messages.create(model=model, max_tokens=max_tokens,  # this SDK version rejects temperature
                               messages=[{"role": "user", "content": content}])
    text = "".join(b.text for b in r.content if b.type == "text")
    return text, "stop" if r.stop_reason == "end_turn" else "length"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=f"/data/{os.environ.get('USER')}/train_data/ViRL39K")
    ap.add_argument("--contamination", default=None)
    ap.add_argument("--ids_file", default=None, help="only these question ids; default: --n_questions from the pool")
    ap.add_argument("--n_questions", type=int, default=2000)
    ap.add_argument("--limit", type=int, default=0, help="cap on API calls this run (cost guard); 0 = all")
    ap.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    ap.add_argument("--base_url", default=None, help="OpenAI-compatible endpoint")
    ap.add_argument("--model", required=True)
    ap.add_argument("--max_tokens", type=int, default=4096)
    ap.add_argument("--max_pixels", type=int, default=1280 * 32 * 32)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry_run", action="store_true", help="build requests for 3 questions, call nothing")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.ids_file:
        want = {l.strip() for l in open(a.ids_file) if l.strip()}
        pool = [q for q in load_pool(a.pool, 10 ** 9, a.seed, a.contamination) if q["id"] in want]
    else:
        pool = load_pool(a.pool, a.n_questions, a.seed, a.contamination)
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in open(out_path)} if out_path.exists() else set()  # resume
    jobs = [q for q in pool if q["id"] not in done]
    if a.limit:
        jobs = jobs[:a.limit]
    agent = f"teacher:{a.model}"
    print(f"{len(pool)} questions, {len(done)} done, {len(jobs)} to call ({agent})", flush=True)

    if a.dry_run:
        for q in jobs[:3]:
            parts = build_parts(q, a.max_pixels)
            print(q["id"], q["gold"], [(k, v if k == "text" else f"<{len(v[1]) // 1024} KiB b64>") for k, v in parts])
        return

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)  # n_tokens in student tokens
    if a.provider == "openai":
        from openai import OpenAI
        client, call = OpenAI(base_url=a.base_url, max_retries=5), call_openai
    else:
        from anthropic import Anthropic
        client, call = Anthropic(max_retries=5), call_anthropic

    def work(q):
        text, finish = call(client, a.model, build_parts(q, a.max_pixels), a.max_tokens)
        pred = final_answer(text)
        return {"id": q["id"], "agent": agent, "category": q["category"], "is_mc": q["is_mc"], "gold": q["gold"],
                "pred": pred, "correct": is_correct(pred, q["gold"], q["is_mc"]), "finish": finish,
                "n_tokens": len(tok(text)["input_ids"]), "question": q["question"], "images": q["images"],
                "response": text}

    lock, n_ok, n_err, t0 = threading.Lock(), 0, 0, time.time()
    with open(out_path, "a") as f, ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(work, q): q for q in jobs}
        for i, fu in enumerate(as_completed(futs), 1):
            try:
                r = fu.result()
            except Exception as e:  # failed calls are not written, so a rerun retries them
                n_err += 1
                print(f"error {futs[fu]['id']}: {type(e).__name__}: {e}", flush=True)
                continue
            with lock:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
                n_ok += r["correct"]
            if i % 50 == 0 or i == len(jobs):
                print(f"[{i}/{len(jobs)}] correct {n_ok}, errors {n_err}, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
