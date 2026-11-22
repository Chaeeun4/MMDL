"""
Rejection-sampling data for fine-tuning (RFT / self-distillation) from a public,
non-MMMU training pool (ViRL39K), using several independent "agents" = prompt
strategies of the SAME base model (Qwen3-VL-4B-Instruct, no external model/API).

Why several strategies: a homogeneous sampler keeps producing the same kind of
answer; diverse strategies cover more questions correctly (higher pass@k) and
give the fine-tuned model more than one way to reach an answer. The agents never
see each other's outputs (independent sampling, no debate), and only the
fine-tuned single model with a single prompt is evaluated, so this is a data
source for fine-tuning, not an inference-time ensemble.

    # 1) generate (GPU, vLLM)
    python code/gen_rft.py generate --pool /data/$USER/train_data/ViRL39K \
        --n_questions 2000 --out /data/$USER/rft/pilot/gen.jsonl
    # 2) filter + write SFT jsonl (format of code/lora_smoke_train.py --train_jsonl) and DPO pairs
    python code/gen_rft.py select --gen /data/$USER/rft/pilot/gen.jsonl --out_dir /data/$USER/rft/pilot
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompt import DESCRIPT_MC, DESCRIPT_OPEN, MC_DIRECT, OPEN_DIRECT  # noqa: E402

MODEL_NAME = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"

# Each agent = one independent prompt strategy. 'mc' / 'open' instruction.
AGENTS = {
    "describe": {"mc": DESCRIPT_MC, "open": DESCRIPT_OPEN},
    "cot": {
        "mc": "Think step by step, then write the final answer on the last line in the form 'Answer: <letter>'.",
        "open": "Solve the problem step by step, then write the final answer on the last line in the form 'Answer: <value>'.",
    },
    "check": {
        "mc": ("Read the relevant values and labels from the image, check each option against them "
               "and rule out the wrong ones with a short reason, then write the final answer on the "
               "last line in the form 'Answer: <letter>'."),
        "open": ("List the given quantities you read from the image, set up the relation, compute, "
                 "check the result once, then write the final answer on the last line in the form "
                 "'Answer: <value>'."),
    },
    "concise": {
        "mc": "Reason briefly in a few sentences, then write the final answer on the last line in the form 'Answer: <letter>'.",
        "open": "Reason briefly in a few sentences, then write the final answer on the last line in the form 'Answer: <value>'.",
    },
    # round 2: a model already fine-tuned to reason under the official MMMU wording (offc1b) answers with
    # that wording; diversity then comes from --samples, not from different prompts
    "official": {"mc": MC_DIRECT, "open": OPEN_DIRECT},
}
ROUND1_AGENTS = "describe,cot,check,concise"
# The instruction the fine-tuned model is trained (and evaluated) with: one prompt for all agents' data.
TRAIN_INSTRUCTION = {"mc": DESCRIPT_MC, "open": DESCRIPT_OPEN}

KEEP_CATEGORIES_ALL = {"Tables/Diagrams/Charts", "Spatial Reasoning", "Broader STEM Topics",
                       "Social Science", "Commonsense", "(GradeSchool) Science"}
BOXED_RE = re.compile(r"\\boxed\{(.*)\}", re.S)
IMG_TAG_RE = re.compile(r"<image>")


# ---------------------------------------------------------------- pool
def load_pool(pool_dir: str, n: int, seed: int, contamination: str | None, exclude=()):
    import pandas as pd
    df = pd.read_parquet(os.path.join(pool_dir, "39Krelease.parquet"))
    bad = set()
    cpath = contamination or os.path.join(pool_dir, "contamination.json")
    if os.path.exists(cpath):
        bad = set(json.load(open(cpath))["flagged"])
    else:
        raise SystemExit(f"no contamination report at {cpath}; run code/check_contamination.py first")
    df = df[~df.qid.isin(bad)]
    if exclude:  # questions an earlier round already used
        df = df[~df.qid.isin(set(exclude))]
    df = df[df.image.map(len) > 0]
    # non-grade-school + science first (closest to MMMU), then fill with grade-school math/geometry
    pri = df[df.category.isin(KEEP_CATEGORIES_ALL)].sample(frac=1, random_state=seed)
    rest = df[~df.category.isin(KEEP_CATEGORIES_ALL)].sample(frac=1, random_state=seed)
    n_pri = min(len(pri), int(n * 0.75))
    df = pd.concat([pri.head(n_pri), rest.head(n - n_pri)]).sample(frac=1, random_state=seed)
    out = []
    for r in df.itertuples():
        gold = BOXED_RE.search(r.answer)
        gold = (gold.group(1) if gold else r.answer).strip()
        is_mc = bool(re.fullmatch(r"[A-J]", gold))  # options appear as "(A) ..", "A. .." or inline
        k = iter(range(1, 100))
        q = IMG_TAG_RE.sub(lambda _: f"<image {next(k)}>", r.question).strip()
        out.append({"id": r.qid, "question": q, "gold": gold, "is_mc": is_mc, "category": r.category,
                    "source": r.source, "images": [os.path.join(pool_dir, p) for p in r.image]})
    return out


def to_messages(question: str, instruction: str, images, min_px, max_px):
    from PIL import Image
    content, cur, used = [], 0, set()
    for m in re.finditer(r"<image (\d+)>", question):
        if m.start() > cur:
            content.append({"type": "text", "text": question[cur:m.start()]})
        i = int(m.group(1))
        content.append({"type": "image", "image": Image.open(images[i - 1]).convert("RGB"),
                        "min_pixels": min_px, "max_pixels": max_px})
        used.add(i)
        cur = m.end()
    tail = question[cur:] + "\n\n" + instruction
    content.append({"type": "text", "text": tail})
    extra = [{"type": "image", "image": Image.open(p).convert("RGB"), "min_pixels": min_px, "max_pixels": max_px}
             for i, p in enumerate(images, 1) if i not in used]
    return [{"role": "user", "content": extra + content}]


# ---------------------------------------------------------------- grading
def final_answer(resp: str) -> str | None:
    pos = resp.rfind("Answer:")
    if pos < 0:
        return None
    a = resp[pos + len("Answer:"):].strip().split("\n")[0]
    b = BOXED_RE.search(a)
    a = b.group(1) if b else a
    return a.strip().strip("*$ .").strip()


def _num(s: str):
    s = s.replace("$", "").replace(",", "").replace("\\%", "").replace("%", "").replace("^\\circ", "").replace("°", "")
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)(?:\s*[a-zA-Z\\{}^ ]*)?\s*", s)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"\s*\\?d?frac\{(-?\d+)\}\{(\d+)\}\s*", s)
    return float(m.group(1)) / float(m.group(2)) if m and float(m.group(2)) else None


def is_correct(pred: str | None, gold: str, is_mc: bool) -> bool:
    if pred is None:
        return False
    if is_mc:
        m = re.match(r"\(?([A-J])\b\)?", pred)
        return bool(m) and m.group(1) == gold
    pn, gn = _num(pred), _num(gold)
    if pn is not None and gn is not None:
        return math.isclose(pn, gn, rel_tol=1e-2, abs_tol=1e-6)
    norm = lambda x: re.sub(r"[\s\\{}$]|text", "", x.lower())
    return norm(pred) == norm(gold)


# ---------------------------------------------------------------- generate
def generate(a):
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams
    from qwen_vl_utils import process_vision_info

    free = __import__("torch").cuda.mem_get_info()[0] / 2 ** 30
    if free < 20:
        raise SystemExit(f"only {free:.1f} GiB GPU memory free; another job is using the GPU")
    if a.ids_file:  # e.g. resample the questions that had no clean sample
        want = {l.strip() for l in open(a.ids_file) if l.strip()}
        pool = [q for q in load_pool(a.pool, 10 ** 9, a.seed, a.contamination) if q["id"] in want]
    else:
        used = {json.loads(l)["id"] for g in a.exclude_gen for l in open(g)}
        pool = load_pool(a.pool, a.n_questions, a.seed, a.contamination, used)
    agents = a.agents.split(",")
    print(f"questions {len(pool)} x agents {agents} x {a.samples} samples", flush=True)
    processor = AutoProcessor.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)
    llm = LLM(model=a.model_path, revision=MODEL_REVISION if a.model_path == MODEL_NAME else None,
              dtype="bfloat16", gpu_memory_utilization=0.90, max_model_len=a.max_model_len,
              limit_mm_per_prompt={"image": 8}, seed=a.seed)
    sp = SamplingParams(n=a.samples, temperature=0.7, top_p=0.8, top_k=20, presence_penalty=1.5,
                        max_tokens=a.max_tokens, seed=a.seed, stop_token_ids=[151645, 151643])
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():  # resume
        done = {(r["id"], r["agent"]) for r in map(json.loads, open(out_path))}
    jobs = [(q, ag) for q in pool for ag in agents if (q["id"], ag) not in done]
    print(f"{len(jobs)} jobs to run ({len(done)} already done)", flush=True)
    with open(out_path, "a") as f:
        for s in range(0, len(jobs), a.chunk):
            chunk, inputs, t0 = jobs[s:s + a.chunk], [], time.time()
            for q, ag in chunk:
                msgs = to_messages(q["question"], AGENTS[ag]["mc" if q["is_mc"] else "open"], q["images"],
                                   a.min_pixels, a.max_pixels)
                prompt = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
                imgs, _ = process_vision_info(msgs, image_patch_size=processor.image_processor.patch_size)
                inputs.append({"prompt": prompt, "multi_modal_data": {"image": imgs}})
            outs = llm.generate(inputs, sampling_params=sp, use_tqdm=False)
            ntok = 0
            for (q, ag), o in zip(chunk, outs):
                for c in o.outputs:
                    pred = final_answer(c.text)
                    ntok += len(c.token_ids)
                    f.write(json.dumps({"id": q["id"], "agent": ag, "category": q["category"], "is_mc": q["is_mc"],
                                        "gold": q["gold"], "pred": pred, "correct": is_correct(pred, q["gold"], q["is_mc"]),
                                        "finish": c.finish_reason, "n_tokens": len(c.token_ids),
                                        "question": q["question"], "images": q["images"], "response": c.text},
                                       ensure_ascii=False) + "\n")
            f.flush()
            dt = time.time() - t0
            print(f"[{s + len(chunk)}/{len(jobs)}] {dt:.0f}s, {ntok / dt:.0f} tok/s", flush=True)


# ---------------------------------------------------------------- select
LOOP_RE = re.compile(r"\b(wait|but maybe|let me re-?check|hmm)\b", re.I)


BLANK_RE = re.compile(r"image (?:provided |shown |given )?(?:is|appears(?: to be)?) (?:completely |entirely )?"
                      r"(?:blank|empty|black|white)|no visible (?:content|elements)", re.I)


def clean(r, max_tokens, min_tokens=0, drop_blank=False):
    t = r["response"]
    if r["n_tokens"] < min_tokens or (drop_blank and BLANK_RE.search(t)):
        return False  # a bare answer teaches no reasoning; "the image is blank" answers did not read the figure
    return (r["correct"] and r["finish"] == "stop" and r["n_tokens"] <= max_tokens
            and t.rstrip().split("\n")[-1].lstrip("*# ").startswith("Answer:")
            and len(LOOP_RE.findall(t)) <= 2)


def select(a):
    rows = [json.loads(l) for g in a.gen for l in open(g)]
    by_q = defaultdict(list)
    for r in rows:
        by_q[r["id"]].append(r)
    rnd = random.Random(a.seed)
    sft, dpo, stats, no_clean = [], [], defaultdict(int), []
    agent_acc = defaultdict(lambda: [0, 0])
    for qid, rs in by_q.items():
        for r in rs:
            agent_acc[r["agent"]][0] += r["correct"]
            agent_acc[r["agent"]][1] += 1
        pass_rate = sum(r["correct"] for r in rs) / len(rs)
        good = sorted([r for r in rs if clean(r, a.max_tokens, a.min_tokens, a.drop_blank) and r["agent"] not in a.exclude_agents],
                      key=lambda r: r["n_tokens"])
        if not good:
            stats["no_clean_sample"] += 1
            no_clean.append(qid)
            continue
        if pass_rate == 1.0 and rnd.random() > a.keep_easy:  # all agents right: little to learn
            stats["easy_dropped"] += 1
            continue
        kind = "mc" if rs[0]["is_mc"] else "open"
        # shortest-first biases training answers toward very short reasoning (C1);
        # random keeps the natural length distribution of clean answers (C1b)
        cand = good if a.pick == "shortest" else rnd.sample(good, len(good))
        limit = a.per_question if kind == "mc" else a.open_per_question
        picked, seen = [], set()
        for r in cand:  # at most one per agent
            if r["agent"] not in seen:
                picked.append(r)
                seen.add(r["agent"])
            if len(picked) == limit:
                break
        stats[f"kept_pass_{sum(r['correct'] for r in rs)}_of_{len(rs)}"] += 1
        for r in picked:
            sft.append({"id": f"{qid}::{r['agent']}", "images": r["images"],
                        "prompt": r["question"] + "\n\n" + TRAIN_INSTRUCTION[kind],
                        "response": r["response"].strip(), "agent": r["agent"], "pass_rate": pass_rate})
        bad = [r for r in rs if not r["correct"] or r["finish"] != "stop"]
        if bad:  # preference pair: shortest clean correct vs a wrong / truncated one
            rej = max(bad, key=lambda r: r["n_tokens"])
            dpo.append({"id": qid, "images": good[0]["images"],
                        "prompt": good[0]["question"] + "\n\n" + TRAIN_INSTRUCTION[kind],
                        "chosen": good[0]["response"].strip(), "rejected": rej["response"].strip()})
        stats["questions_kept"] += 1
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rnd.shuffle(sft)
    for name, data in (("sft.jsonl", sft), ("dpo.jsonl", dpo)):
        with open(out / name, "w") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    report = {"generations": len(rows), "questions": len(by_q), **stats, "sft_samples": len(sft),
              "dpo_pairs": len(dpo),
              "agent_accuracy": {k: round(c / n, 3) for k, (c, n) in agent_acc.items()},
              "pass_at_1_mean": round(sum(r["correct"] for r in rows) / len(rows), 3),
              "pass_at_any": round(sum(any(r["correct"] for r in rs) for rs in by_q.values()) / len(by_q), 3),
              "sft_mean_tokens": round(sum(len(r["response"]) for r in sft) / max(len(sft), 1) / 4)}
    json.dump(report, open(out / "select_report.json", "w"), indent=1)
    (out / "no_clean_ids.txt").write_text("\n".join(no_clean) + "\n")
    print(json.dumps(report, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--pool", required=True)
    g.add_argument("--contamination", default=None)
    g.add_argument("--model_path", default=MODEL_NAME)
    g.add_argument("--n_questions", type=int, default=2000)
    g.add_argument("--agents", default=ROUND1_AGENTS)
    g.add_argument("--exclude_gen", nargs="*", default=[],
                   help="gen.jsonl files of earlier rounds; their questions are left out of the pool")
    g.add_argument("--samples", type=int, default=1, help="samples per (question, agent)")
    g.add_argument("--max_tokens", type=int, default=2048)
    g.add_argument("--max_model_len", type=int, default=8192)
    g.add_argument("--min_pixels", type=int, default=256 * 32 * 32)
    g.add_argument("--max_pixels", type=int, default=1280 * 32 * 32)
    g.add_argument("--chunk", type=int, default=512)
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--ids_file", default=None, help="only these question ids (one per line)")
    g.add_argument("--out", required=True)
    s = sub.add_parser("select")
    s.add_argument("--gen", required=True, nargs="+")
    s.add_argument("--pick", choices=["shortest", "random"], default="shortest")
    s.add_argument("--exclude_agents", default="", type=lambda x: set(filter(None, x.split(","))),
                   help="agents whose answers are not used for SFT, e.g. 'concise'")
    s.add_argument("--open_per_question", type=int, default=None, help="default: --per_question")
    s.add_argument("--out_dir", required=True)
    s.add_argument("--max_tokens", type=int, default=1500)
    s.add_argument("--min_tokens", type=int, default=0, help="drop answers shorter than this (bare answers)")
    s.add_argument("--drop_blank", action="store_true", help="drop answers that call the image blank / missing")
    s.add_argument("--per_question", type=int, default=2)
    s.add_argument("--keep_easy", type=float, default=0.3)
    s.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "select" and a.open_per_question is None:
        a.open_per_question = a.per_question
    generate(a) if a.cmd == "generate" else select(a)


if __name__ == "__main__":
    main()
