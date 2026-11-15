"""
Build the Chemistry + Music fine-tuning mix (never MMMU / MMMU-Pro data).

Sources
  chem   /data/$USER/train_data/chem_labels/labels   molecule image -> atoms with 3D coordinates
  music  /data/$USER/train_data/primus_training_5000 PrIMuS incipit image -> semantic tokens
  replay /data/$USER/rft/c1b/sft.jsonl               general ViRL39K RFT data (keeps the other subjects)

From the labels we derive image-grounded questions in the same describe_cot format the
model is evaluated with (description -> reasoning -> 'Answer: X'), plus a smaller share
of the original tasks (3D coordinates, full transcription):
  chem_qa     element counts, non-hydrogen formula, ring count, absent element
  chem_coord  original task: 3D coordinates
  music_qa    clef, key signature, time signature, first pitch, interval, duration, counts
  music_trans original task: PrIMuS semantic transcription

Compliance: every prompt is text-checked against MMMU (dev/val/test) + MMMU-Pro and every
chem/music image is dHash-checked against all MMMU Chemistry/Music images; hits are dropped
and listed in contamination_report.json.

    python code/build_cm_data.py --out_dir /data/$USER/rft/cm
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompt import DESCRIPT_MC, DESCRIPT_OPEN  # noqa: E402

USER = os.environ.get("USER", "jinagg")
LETTERS = "ABCDEFGH"


def mc_prompt(question, options):
    choices = "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(options))
    return f"{question}\n\n{choices}\n{DESCRIPT_MC}"


def open_prompt(question):
    return f"{question}\n\n{DESCRIPT_OPEN}"


def make_qa(rng, rid, image, src, kind, question, describe, reason, answer, distractors, open_ok=False):
    """One record. `distractors` are wrong options (strings); open_ok allows the open form."""
    distractors = [d for d in dict.fromkeys(map(str, distractors)) if d != str(answer)]
    if open_ok and (len(distractors) < 3 or rng.random() < 0.2):
        prompt = open_prompt(question)
        resp = f"{describe}\n\n{reason}\n\nAnswer: {answer}"
    else:
        if len(distractors) < 3:
            return None
        opts = rng.sample(distractors, 3) + [str(answer)]
        rng.shuffle(opts)
        letter = LETTERS[opts.index(str(answer))]
        prompt = mc_prompt(question, opts)
        resp = f"{describe}\n\n{reason} This matches option ({letter}).\n\nAnswer: {letter}"
    return {"id": f"{src}::{rid}::{kind}", "images": [image], "prompt": prompt, "response": resp,
            "src": src, "kind": kind}


# ------------------------------------------------------------------ chemistry
ELEM = {"C": "carbon", "N": "nitrogen", "O": "oxygen", "F": "fluorine", "Cl": "chlorine", "S": "sulfur",
        "Br": "bromine", "I": "iodine", "Si": "silicon", "P": "phosphorus", "H": "hydrogen"}
RADIUS = {"C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57, "Cl": 1.02, "S": 1.05, "Br": 1.20, "I": 1.39,
          "Si": 1.11, "P": 1.07, "H": 0.31}


def parse_atoms(text):
    atoms = []
    for line in text.strip().split("\n"):
        p = line.split()
        if len(p) != 4 or p[0] not in ELEM:
            return None
        atoms.append((p[0], float(p[1]), float(p[2]), float(p[3])))
    return atoms


def ring_count(heavy):
    """Cyclomatic number (= number of smallest rings) of the distance-derived heavy-atom graph."""
    n = len(heavy)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    edges = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = math.dist(heavy[i][1:], heavy[j][1:])
            if d < RADIUS[heavy[i][0]] + RADIUS[heavy[j][0]] + 0.40:
                edges += 1
                parent[find(i)] = find(j)
    comps = len({find(i) for i in range(n)})
    return edges - n + comps


def formula(cnt):
    order = (["C"] if "C" in cnt else []) + sorted(e for e in cnt if e != "C")
    return "".join(f"{e}{cnt[e] if cnt[e] > 1 else ''}" for e in order)


def chem_qa(rng, rid, image, atoms):
    heavy = [a for a in atoms if a[0] != "H"]
    cnt = Counter(a[0] for a in heavy)
    rings = ring_count(heavy)
    order = (["C"] if "C" in cnt else []) + sorted(e for e in cnt if e != "C")
    listing = ", ".join(f"{cnt[e]} {ELEM[e]} ({e})" for e in order)
    describe = (f"The image shows the skeletal structural formula of one molecule. Counting every vertex, "
                f"line end and labelled atom, the non-hydrogen atoms are: {listing}, {len(heavy)} in total. "
                f"The skeleton closes {rings} ring{'s' if rings != 1 else ''}.")
    kinds = ["count", "count", "formula", "rings", "total"]
    if len(cnt) >= 3:
        kinds.append("absent")
    kind = rng.choice(kinds)
    if kind == "count":
        e = rng.choice(order if rng.random() < 0.3 else ([x for x in order if x != "C"] or order))
        v = cnt[e]
        q = f"<image 1> How many {ELEM[e]} atoms does the molecule shown contain?"
        cand = [x for x in {v - 2, v - 1, v + 1, v + 2, v + 3} if x >= 0]
        return make_qa(rng, rid, image, "chem_qa", f"count_{e}", q, describe,
                       f"The structure contains {v} {ELEM[e]} atom{'s' if v != 1 else ''}.", v, cand, open_ok=True)
    if kind == "formula":
        q = ("<image 1> Which formula gives the correct numbers of non-hydrogen atoms in the molecule shown "
             "(hydrogens omitted)?")
        wrong = set()
        for _ in range(40):
            c2 = Counter(cnt)
            for e in rng.sample(order, k=min(len(order), rng.choice([1, 1, 2]))):
                c2[e] = max(1, c2[e] + rng.choice([-2, -1, 1, 2]))
            if c2 != cnt:
                wrong.add(formula(c2))
        return make_qa(rng, rid, image, "chem_qa", "formula", q, describe,
                       f"Without hydrogens the atom counts give {formula(cnt)}.", formula(cnt), sorted(wrong))
    if kind == "rings":
        q = "<image 1> How many rings does the molecule shown contain?"
        cand = [x for x in {rings - 2, rings - 1, rings + 1, rings + 2, rings + 3} if x >= 0]
        return make_qa(rng, rid, image, "chem_qa", "rings", q, describe,
                       f"The number of rings is {rings}.", rings, cand, open_ok=True)
    if kind == "total":
        v = len(heavy)
        q = "<image 1> How many non-hydrogen (heavy) atoms does the molecule shown contain?"
        return make_qa(rng, rid, image, "chem_qa", "total", q, describe,
                       f"The total number of non-hydrogen atoms is {v}.", v,
                       [v - 3, v - 2, v - 1, v + 1, v + 2, v + 3], open_ok=True)
    absent = rng.choice([e for e in ["N", "O", "S", "F", "Cl", "Br", "P"] if e not in cnt])
    q = "<image 1> Which of the following elements does NOT appear in the molecule shown?"
    present = [ELEM[e] for e in order]
    return make_qa(rng, rid, image, "chem_qa", "absent", q, describe,
                   f"The molecule contains {', '.join(present)}, but no {ELEM[absent]}.", ELEM[absent], present)


def load_chem(root):
    root = Path(root)
    out = []
    for line in open(root / "train.jsonl", encoding="utf-8"):
        r = json.loads(line)
        img = root / "images" / f"{r['id']}.png"
        atoms = parse_atoms(r["conversations"][1]["content"])
        if atoms and img.exists():
            out.append({"id": r["id"], "image": str(img), "atoms": atoms,
                        "task": r["conversations"][0]["content"], "label": r["conversations"][1]["content"]})
    return out


# ---------------------------------------------------------------------- music
CLEF = {"G2": "treble (G) clef", "G1": "French violin clef (G clef on the first line)", "F4": "bass (F) clef",
        "F3": "baritone clef (F clef on the third line)", "C1": "soprano clef (C clef on the first line)",
        "C2": "mezzo-soprano clef (C clef on the second line)", "C3": "alto clef (C clef on the third line)",
        "C4": "tenor clef (C clef on the fourth line)", "C5": "baritone clef (C clef on the fifth line)"}
KEYS = {"CM": 0, "GM": 1, "DM": 2, "AM": 3, "EM": 4, "BM": 5, "F#M": 6, "C#M": 7,
        "FM": -1, "BbM": -2, "EbM": -3, "AbM": -4, "DbM": -5, "GbM": -6, "CbM": -7}
TIME_POOL = ["2/4", "3/4", "4/4", "2/2", "3/8", "6/8", "9/8", "12/8", "3/2", "6/4", "4/2", "2/8", "4/8"]
STEP = "CDEFGAB"
SEMI = [0, 2, 4, 5, 7, 9, 11]
NUM = ["unison", "second", "third", "fourth", "fifth", "sixth", "seventh", "octave"]
PITCH_RE = re.compile(r"^([A-G])(#{1,2}|b{1,2})?(\d)$")
DURS = ["whole", "half", "quarter", "eighth", "sixteenth", "thirty second", "dotted half", "dotted quarter",
        "dotted eighth", "dotted sixteenth"]


def key_name(k):
    n = KEYS[k]
    acc = "no sharps or flats" if n == 0 else f"{abs(n)} {'sharp' if n > 0 else 'flat'}{'s' if abs(n) > 1 else ''}"
    return f"{k[:-1].replace('b', '-flat').replace('#', '-sharp')} major ({acc})"


def time_name(t):
    return {"C": "4/4", "C/": "2/2"}.get(t, t)


def dur_name(d):
    d = d.replace("_fermata", "")
    dots = len(d) - len(d.rstrip("."))
    base = d.rstrip(".").replace("_", " ")
    return ("double dotted " if dots == 2 else "dotted " if dots == 1 else "") + base


def pitch_info(p):
    m = PITCH_RE.match(p)
    if not m:
        return None
    letter, acc, octv = m.group(1), m.group(2) or "", int(m.group(3))
    i = STEP.index(letter)
    alter = acc.count("#") - acc.count("b")
    return {"name": p, "dia": octv * 7 + i, "midi": 12 * (octv + 1) + SEMI[i] + alter}


def interval_name(a, b):
    steps, semis = abs(b["dia"] - a["dia"]), abs(b["midi"] - a["midi"])
    if steps > 7 or (b["dia"] - a["dia"]) * (b["midi"] - a["midi"]) < 0:
        return None
    base = SEMI[steps % 7] + 12 * (steps // 7)
    diff = semis - base
    if steps % 7 in (0, 3, 4):
        qual = {0: "perfect", 1: "augmented", -1: "diminished"}.get(diff)
    else:
        qual = {0: "major", -1: "minor", 1: "augmented", -2: "diminished"}.get(diff)
    if qual is None:
        return None
    return f"{qual} {NUM[steps]}"


def parse_music(tokens):
    info = {"clef": None, "key": "CM", "time": None, "events": [], "first_measure": [], "ok": True}
    in_first = True
    for t in tokens.split():
        head, _, rest = t.partition("-")
        if head == "clef" and info["clef"] is None:
            info["clef"] = rest
        elif head == "keySignature" and not info["events"]:
            info["key"] = rest
        elif head == "timeSignature" and info["time"] is None:
            info["time"] = rest
        elif head == "barline":
            in_first = False
        elif head in ("note", "gracenote"):
            pitch, _, dur = rest.partition("_")
            pi = pitch_info(pitch)
            if pi is None:
                info["ok"] = False
                continue
            ev = dict(pi, dur=dur_name(dur), grace=head == "gracenote")
            info["events"].append(ev)
            if in_first:
                info["first_measure"].append(ev)
    return info


def music_qa(rng, rid, image, tokens):
    m = parse_music(tokens)
    if not m["ok"] or m["clef"] not in CLEF or m["key"] not in KEYS:
        return None
    notes = [e for e in m["events"] if not e["grace"]]
    if len(notes) < 2:
        return None
    head = f"The staff begins with a {CLEF[m['clef']]}"
    head += f", a key signature of {key_name(m['key']).split('(')[1].rstrip(')')}"
    head += f" and the time signature {m['time']}" + (
        f" (= {time_name(m['time'])})" if m["time"] in ("C", "C/") else "") if m["time"] else " and no time signature"
    fm = (m["first_measure"] if len(m["first_measure"]) >= 2 else m["events"][:8])[:12]
    seq = ", ".join(f"{e['name']} {e['dur']}" + (" (grace)" if e["grace"] else "") for e in fm)
    describe = f"The image shows one staff of printed music. {head}. Reading the first notes in order: {seq}."
    kinds = ["key", "key", "time", "clef", "first", "first", "interval", "interval", "duration", "count", "highest"]
    kind = rng.choice(kinds)
    if kind == "time" and not m["time"]:
        kind = "first"
    mk = lambda *a, **k: make_qa(rng, rid, image, "music_qa", kind, *a, **k)  # noqa: E731
    if kind == "key":
        if rng.random() < 0.5:
            n = KEYS[m["key"]]
            ans = "no sharps or flats" if n == 0 else f"{abs(n)} {'sharp' if n > 0 else 'flat'}{'s' if abs(n) > 1 else ''}"
            pool = ["no sharps or flats"] + [f"{i} {s}{'s' if i > 1 else ''}" for i in range(1, 6) for s in ("sharp", "flat")]
            near = [p for p in pool if p != ans]
            return mk("<image 1> How many sharps or flats are in the key signature of this excerpt?", describe,
                      f"The key signature has {ans}.", ans, rng.sample(near, 5))
        ans = key_name(m["key"]).split(" (")[0]
        pool = [key_name(k).split(" (")[0] for k in KEYS if abs(KEYS[k] - KEYS[m["key"]]) <= 3 and k != m["key"]]
        return mk("<image 1> Which major key has the key signature shown in this excerpt?", describe,
                  f"A key signature of {key_name(m['key']).split('(')[1].rstrip(')')} belongs to {ans}.", ans, pool)
    if kind == "time":
        ans = time_name(m["time"])
        if ans not in TIME_POOL:
            return None
        return mk("<image 1> What is the time signature of this excerpt?", describe,
                  f"The time signature is {ans}.", ans, [t for t in TIME_POOL if t != ans][:8])
    if kind == "clef":
        return mk("<image 1> Which clef is used at the beginning of this staff?", describe,
                  f"The clef is a {CLEF[m['clef']]}.", CLEF[m["clef"]], [v for k, v in CLEF.items() if k != m["clef"]])
    first = notes[0]
    if kind == "first":
        acc = re.sub(r"[A-G0-9]", "", first["name"])  # distractors carry the same accidental: no giveaway
        near = [first["name"].replace(acc, "")] if acc else []
        for d in (-3, -2, -1, 1, 2, 3):
            dia = first["dia"] + d
            near.append(f"{STEP[dia % 7]}{acc}{dia // 7}")
        return mk("<image 1> What is the pitch (letter name and octave, middle C = C4) of the first note of this "
                  "excerpt, ignoring grace notes?", describe,
                  f"Read against the clef and key signature, the first note is {first['name']}.", first["name"],
                  near, open_ok=True)
    if kind == "interval":
        a, b = notes[0], notes[1]
        ans = interval_name(a, b)
        if ans is None:
            return None
        direction = "the same pitch" if a["midi"] == b["midi"] else ("upward" if b["midi"] > a["midi"] else "downward")
        pool = ["perfect unison", "minor second", "major second", "minor third", "major third", "perfect fourth",
                "augmented fourth", "perfect fifth", "minor sixth", "major sixth", "minor seventh", "major seventh",
                "perfect octave"]
        idx = pool.index(ans) if ans in pool else 6
        near = [p for i, p in enumerate(pool) if p != ans and abs(i - idx) <= 4]
        return mk("<image 1> What is the interval between the first two notes of this excerpt (ignoring grace notes)?",
                  describe, f"The first two notes are {a['name']} and {b['name']}, moving {direction}: "
                  f"a {ans}.", ans, near)
    if kind == "duration":
        ans = first["dur"]
        if ans not in DURS:
            return None
        return mk("<image 1> What is the note value (duration) of the first note of this excerpt, ignoring grace notes?",
                  describe, f"The first note {first['name']} is a {ans} note.", ans, [d for d in DURS if d != ans][:9])
    if kind == "count":
        v = len([e for e in m["first_measure"] if not e["grace"]])
        if v == 0 or len(m["first_measure"]) > 12:
            return None
        return mk("<image 1> How many notes (not counting rests or grace notes) are in the first measure of this "
                  "excerpt?", describe, f"The first measure contains {v} note{'s' if v != 1 else ''}.", v,
                  [x for x in (v - 2, v - 1, v + 1, v + 2, v + 3) if x > 0], open_ok=True)
    top = max(notes, key=lambda e: e["midi"])
    allp = list(dict.fromkeys(e["name"] for e in notes))
    full = ", ".join(e["name"] for e in notes[:40])
    return mk("<image 1> What is the highest pitch that occurs in this excerpt (middle C = C4), ignoring grace notes?",
              describe + f" All note pitches in order: {full}.", f"The highest of these is {top['name']}.", top["name"],
              [p for p in allp if p != top["name"]], open_ok=True) if len(notes) <= 40 else None


def load_music(root, split):
    root = Path(root)
    out = []
    for line in open(root / "primus_jsonl" / f"{split}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        img = root / r["images"][0]
        if img.exists():
            out.append({"id": img.stem, "image": str(img), "task": r["messages"][0]["content"],
                        "label": r["messages"][1]["content"]})
    return out


def raw_task(item, src):
    """The original task of the uploaded data, unchanged apart from the image tag."""
    return {"id": f"{src}::{item['id']}", "images": [item["image"]], "src": src, "kind": "original",
            "prompt": item["task"].replace("<image>", "<image 1>", 1), "response": item["label"]}


# ---------------------------------------------------------------- compliance
def dhash(path, size=16):
    from PIL import Image
    im = path if not isinstance(path, (str, Path)) else Image.open(path)
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    im = Image.alpha_composite(bg, im).convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(im.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (px[r * (size + 1) + c] > px[r * (size + 1) + c + 1])
    return bits


def contamination(records, data_root, max_bits=10):
    """Returns ids to drop + a report. Text: exact / 8-gram overlap; images: dHash vs MMMU Chemistry+Music."""
    from datasets import load_dataset
    from check_contamination import norm, shingles
    from dataset import DATASET_NAME, DATASET_REVISION, SUBJECTS
    exact, index, img_hashes = {}, defaultdict(set), {}
    n_bench = 0
    for subj in SUBJECTS:
        for split in ("dev", "validation", "test"):
            ds = load_dataset(DATASET_NAME, subj, split=split, revision=DATASET_REVISION, cache_dir=data_root)
            for bid, q, o in zip(ds["id"], ds["question"], ds["options"]):
                t = norm(q + " " + str(o))
                n_bench += 1
                exact.setdefault(t, bid)
                for s in shingles(t):
                    index[s].add(bid)
            if subj in ("Chemistry", "Music"):
                for row in ds:
                    for k in range(1, 8):
                        if row.get(f"image_{k}") is not None:
                            img_hashes[dhash(row[f"image_{k}"])] = row["id"]
    pro = "not loaded"
    try:
        for cfg in ("standard (10 options)", "standard (4 options)"):
            ds = load_dataset("MMMU/MMMU_Pro", cfg, split="test", cache_dir=data_root)
            for bid, q, o in zip(ds["id"], ds["question"], ds["options"]):
                t = norm(q + " " + str(o))
                exact.setdefault(t, f"pro::{bid}")
                for s in shingles(t):
                    index[s].add(f"pro::{bid}")
        pro = "loaded"
    except Exception as e:  # MMMU-Pro questions are MMMU test questions, which are covered above
        pro = f"not loaded ({type(e).__name__})"
    flagged = {}
    cache = {}
    bench_h = list(img_hashes)
    for r in records:
        if r["src"] == "replay":
            continue
        t = norm(r["prompt"].replace(DESCRIPT_MC, "").replace(DESCRIPT_OPEN, ""))
        if t in exact:
            flagged[r["id"]] = {"kind": "text exact", "match": exact[t]}
            continue
        sh = shingles(t)
        hits = Counter(b for s in sh for b in index.get(s, ()))
        if hits and hits.most_common(1)[0][1] / len(sh) >= 0.5:
            flagged[r["id"]] = {"kind": "text 8gram", "match": hits.most_common(1)[0][0]}
            continue
        p = r["images"][0]
        if p not in cache:
            h = dhash(p)
            best = min(((bin(h ^ b).count("1"), b) for b in bench_h), default=(999, None))
            cache[p] = best
        if cache[p][0] <= max_bits:
            flagged[r["id"]] = {"kind": f"image dhash {cache[p][0]} bits", "match": img_hashes[cache[p][1]]}
    report = {"benchmark_questions": n_bench, "benchmark_chem_music_images": len(img_hashes), "mmmu_pro": pro,
              "checked_records": sum(r["src"] != "replay" for r in records), "checked_images": len(cache),
              "min_image_distance_bits": min((v[0] for v in cache.values()), default=None),
              "n_flagged": len(flagged), "flagged": flagged}
    return set(flagged), report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chem", default=f"/data/{USER}/train_data/chem_labels/labels")
    ap.add_argument("--music", default=f"/data/{USER}/train_data/primus_training_5000")
    ap.add_argument("--replay", default=f"/data/{USER}/rft/c1b/sft.jsonl")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--n_chem_qa", type=int, default=3000)
    ap.add_argument("--n_chem_coord", type=int, default=500)
    ap.add_argument("--n_music_qa", type=int, default=3000)
    ap.add_argument("--n_music_trans", type=int, default=1000)
    ap.add_argument("--n_val", type=int, default=60, help="held-out records per source for the loss curve")
    ap.add_argument("--data_root", default=os.environ.get("HF_HOME"))
    ap.add_argument("--skip_check", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    chem = load_chem(a.chem)
    rng.shuffle(chem)
    music_tr = load_music(a.music, "train")
    music_va = load_music(a.music, "val")
    rng.shuffle(music_tr)
    replay = [dict(json.loads(l), src="replay") for l in open(a.replay, encoding="utf-8") if l.strip()]
    rng.shuffle(replay)
    print(f"chem {len(chem)}, music train {len(music_tr)} / val {len(music_va)}, replay {len(replay)}")

    def take(items, n, fn):
        got, used = [], 0
        for it in items:
            if len(got) >= n:
                break
            used += 1
            r = fn(it)
            if r:
                got.append(r)
        return got, items[used:]

    # disjoint molecules / scores for train vs held-out; QA and original task use different items
    c_qa, rest = take(chem, a.n_chem_qa, lambda c: chem_qa(rng, c["id"], c["image"], c["atoms"]))
    c_co, rest = take(rest, a.n_chem_coord, lambda c: raw_task(c, "chem_coord"))
    v_cqa, rest = take(rest, a.n_val, lambda c: chem_qa(rng, c["id"], c["image"], c["atoms"]))
    v_cco, rest = take(rest, a.n_val, lambda c: raw_task(c, "chem_coord"))
    m_qa, mrest = take(music_tr, a.n_music_qa, lambda m: music_qa(rng, m["id"], m["image"], m["label"]))
    m_tr, mrest = take(mrest, a.n_music_trans, lambda m: raw_task(m, "music_trans"))
    v_mqa, vrest = take(music_va, a.n_val, lambda m: music_qa(rng, m["id"], m["image"], m["label"]))
    v_mtr, vrest = take(vrest, a.n_val, lambda m: raw_task(m, "music_trans"))
    # replay hold-out by question, so no held-out question is also trained on under another agent
    val_q = set()
    for r in replay:
        if len(val_q) >= a.n_val:
            break
        val_q.add(r["id"].split("::")[0])
    v_rep = [r for r in replay if r["id"].split("::")[0] in val_q][:a.n_val]
    t_rep = [r for r in replay if r["id"].split("::")[0] not in val_q]

    train = c_qa + c_co + m_qa + m_tr + t_rep
    val = v_cqa + v_cco + v_mqa + v_mtr + v_rep
    report = {"skipped": True}
    if not a.skip_check:
        drop, report = contamination(train + val, a.data_root)
        train = [r for r in train if r["id"] not in drop]
        val = [r for r in val if r["id"] not in drop]
        print(f"contamination: flagged {len(drop)} (min image distance {report['min_image_distance_bits']} bits)")
    json.dump(report, open(out / "contamination_report.json", "w"), indent=1)
    rng.shuffle(train)
    for name, recs in (("train", train), ("val", val)):
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats = {"train": dict(Counter(r["src"] for r in train)), "val": dict(Counter(r["src"] for r in val)),
             "train_total": len(train),
             "kinds": dict(Counter(f"{r['src']}/{r['kind'].split('_')[0]}" for r in train if r["src"] != "replay")),
             "mc_answer_letters": dict(Counter(r["response"][-1] for r in train
                                               if r["src"].endswith("_qa") and DESCRIPT_MC in r["prompt"]))}
    json.dump(stats, open(out / "build_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
