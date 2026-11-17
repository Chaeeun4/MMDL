"""
Synthetic "read the figure" training data, drawn from scratch (no MMMU / MMMU-Pro content is used):
  music : notes on a staff rendered with Verovio  -> note name, interval, chord, scale degree,
          key signature, bar count, time signature, total duration
  chem  : skeletal formulas rendered with RDKit from public SMILES lists (BBBP, ESOL)
          -> number of stereocenters, R/S of a marked centre, number of stereoisomers,
             relationship of two drawings, molecular formula
  plot  : matplotlib figures -> phase diagram regions/lines, titration curve type and equivalence point,
          calibration line read-off, table calculation
Every answer is computed by the generator, so labels are exact. The prompt is the official MMMU wording
(prompt.py MC_DIRECT / OPEN_DIRECT) and the response is a short worked solution ending in 'Answer: X'.
The question TYPES were chosen after an error analysis of MMMU-val; no benchmark question, image, number
or option is copied, and every image is dHash-checked against all MMMU images.

    python code/build_percept_data.py --out_dir /data/$USER/rft/percept --n_music 3000 --n_chem 2000 --n_plot 1500
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompt import MC_DIRECT, OPEN_DIRECT  # noqa: E402

USER = os.environ.get("USER", "user")
LETTERS = "ABCDEFGHIJ"
ORD = ["zeroth", "first", "second", "third", "fourth", "fifth", "sixth"]


# ----------------------------------------------------------------------------- common
def record(rng, rid, src, kind, question, solution, answer, options=None, fixed=False):
    """options: list containing the answer (None = open question). fixed keeps the option order."""
    q = f"<image 1>\n{question}" if rng.random() < 0.5 else f"{question} <image 1>"
    if options is None:
        return {"id": rid, "prompt": f"{q}\n\n{OPEN_DIRECT}", "response": f"{solution}\n\nAnswer: {answer}",
                "src": src, "kind": kind}
    opts = list(dict.fromkeys(map(str, options)))
    if str(answer) not in opts or len(opts) < 2:
        return None
    if not fixed:
        rng.shuffle(opts)
    letter = LETTERS[opts.index(str(answer))]
    choices = "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(opts))
    return {"id": rid, "prompt": f"{q}\n\n{choices}\n{MC_DIRECT}",
            "response": f"{solution}\n\nThis is option ({letter}).\n\nAnswer: {letter}", "src": src, "kind": kind}


def scan_like(rng, img, strength=1.0):
    """Random size / blur / JPEG noise / margin so the images do not all share one clean look."""
    from PIL import Image, ImageFilter, ImageOps
    img = img.convert("RGB")
    f = rng.uniform(0.7, 1.5)
    img = img.resize((max(32, int(img.width * f)), max(32, int(img.height * f))), Image.BICUBIC)
    if rng.random() < 0.4 * strength:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 1.1)))
    if rng.random() < 0.3 * strength:
        img = ImageOps.grayscale(img).convert("RGB")
    if rng.random() < 0.5 * strength:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=rng.randint(35, 90))
        img = Image.open(io.BytesIO(buf.getvalue())).convert("RGB")
    pad = [rng.randint(4, 40) for _ in range(4)]
    out = Image.new("RGB", (img.width + pad[0] + pad[2], img.height + pad[1] + pad[3]), "white")
    out.paste(img, (pad[0], pad[1]))
    return out


# ----------------------------------------------------------------------------- music
STEPS = "CDEFGAB"
NAT = [0, 2, 4, 5, 7, 9, 11]
ACC = {-1: "b", 0: "", 1: "#"}
MEI_ACC = {-1: "f", 0: "n", 1: "s"}
CLEFS = {  # name: (shape, line, diatonic number of the bottom line, wording, anchor sentence)
    "treble": ("G", 2, 30, "treble (G) clef", "its second line is G4, so the bottom line is E4"),
    "bass": ("F", 4, 18, "bass (F) clef", "its fourth line is F3, so the bottom line is G2"),
    "alto": ("C", 3, 24, "alto (C) clef", "its middle line is middle C (C4), so the bottom line is F3"),
    "tenor": ("C", 4, 22, "tenor (C) clef", "its fourth line is middle C (C4), so the bottom line is D3"),
}
SHARP_ORDER, FLAT_ORDER = "FCGDAEB", "BEADGCF"
MAJOR_KEYS = {0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", -1: "F", -2: "Bb", -3: "Eb", -4: "Ab", -5: "Db"}
MINOR_KEYS = {0: "A", 1: "E", 2: "B", 3: "F#", 4: "C#", 5: "G#", -1: "D", -2: "G", -3: "C", -4: "F", -5: "Bb"}
DEGREES = ["tonic", "supertonic", "mediant", "subdominant", "dominant", "submediant", "leading note"]
DUR_NAME = {1: "whole", 2: "half", 4: "quarter", 8: "eighth", 16: "sixteenth"}
CHORDS = {
    "major triad": [0, 4, 7], "minor triad": [0, 3, 7], "diminished triad": [0, 3, 6], "augmented triad": [0, 4, 8],
    "major seventh chord": [0, 4, 7, 11], "dominant (major-minor) seventh chord": [0, 4, 7, 10],
    "minor seventh chord": [0, 3, 7, 10], "half-diminished seventh chord": [0, 3, 6, 10],
    "diminished seventh chord": [0, 3, 6, 9],
}
INVERSIONS = ["root position", "first inversion", "second inversion", "third inversion"]


def p_name(step, acc, octave=None):
    return f"{STEPS[step]}{ACC[acc]}{'' if octave is None else octave}"


def p_semi(step, acc, octave):
    return octave * 12 + NAT[step] + acc


def key_acc(step, n):
    if n > 0 and STEPS[step] in SHARP_ORDER[:n]:
        return 1
    if n < 0 and STEPS[step] in FLAT_ORDER[:-n]:
        return -1
    return 0


def key_text(n):
    if n == 0:
        return "no key signature"
    names = SHARP_ORDER[:n] if n > 0 else FLAT_ORDER[:-n]
    sym = "#" if n > 0 else "b"
    return f"a key signature of {abs(n)} {'sharp' if n > 0 else 'flat'}{'s' if abs(n) > 1 else ''} ({', '.join(c + sym for c in names)})"


def pos_text(pos):
    if 0 <= pos <= 8:
        return f"on the {ORD[pos // 2 + 1]} line" if pos % 2 == 0 else f"in the {ORD[(pos + 1) // 2]} space"
    side, k = ("below", -pos) if pos < 0 else ("above", pos - 8)
    if k % 2 == 0:
        return f"on the {ORD[k // 2]} ledger line {side} the staff"
    return f"in the space just {side} the staff" if k == 1 else \
        f"in the space beyond the {ORD[(k - 1) // 2]} ledger line {side} the staff"


def rand_note(rng, clef, lo=-4, hi=12, key=0, p_acc=0.3):
    """A note at a random staff position. Returns dict with the displayed and the sounding accidental."""
    d = CLEFS[clef][2] + rng.randint(lo, hi)
    step, octave = d % 7, d // 7
    shown = rng.choice([-1, 1]) if rng.random() < p_acc else None
    if shown is not None and key_acc(step, key) == shown:
        shown = None
    acc = shown if shown is not None else key_acc(step, key)
    return {"step": step, "oct": octave, "acc": acc, "shown": shown, "pos": d - CLEFS[clef][2], "d": d}


def note_xml(n, dur=1, dots=0):
    a = f' accid="{MEI_ACC[n["shown"]]}"' if n.get("shown") is not None else ""
    dd = f' dots="{dots}"' if dots else ""
    return f'<note pname="{STEPS[n["step"]].lower()}" oct="{n["oct"]}" dur="{dur}"{dd}{a}/>'


def chord_xml(notes, dur=1):
    inner = "".join(note_xml(n, dur).replace(f' dur="{dur}"', "") for n in notes)
    return f'<chord dur="{dur}">{inner}</chord>'


def read_text(n, clef):
    """How the pitch is read off the staff."""
    t = f"the note {pos_text(n['pos'])} is {STEPS[n['step']]}{n['oct']}"
    if n.get("shown") is not None:
        t += f", and the {'sharp' if n['shown'] > 0 else 'flat'} in front of it makes it {p_name(n['step'], n['acc'], n['oct'])}"
    elif n["acc"]:
        t += f", which the key signature turns into {p_name(n['step'], n['acc'], n['oct'])}"
    return t


def mei_doc(staves, key=0, meter=None, brace=False):
    """staves: list of (clef, [measure, ...]); a measure is a list of event xml strings."""
    ks = "0" if key == 0 else f"{abs(key)}{'s' if key > 0 else 'f'}"
    mt = f' meter.count="{meter[0]}" meter.unit="{meter[1]}"' if meter else ""
    defs = "".join(f'<staffDef n="{i + 1}" lines="5" clef.shape="{CLEFS[c][0]}" clef.line="{CLEFS[c][1]}" key.sig="{ks}"{mt}/>'
                   for i, (c, _) in enumerate(staves))
    n_meas = len(staves[0][1])
    body = ""
    for m in range(n_meas):
        right = ' right="end"' if m == n_meas - 1 else ""
        body += f'<measure n="{m + 1}"{right}>' + "".join(
            f'<staff n="{i + 1}"><layer n="1">{"".join(ms[m])}</layer></staff>' for i, (_, ms) in enumerate(staves)) + "</measure>"
    grp = '<staffGrp symbol="brace" bar.thru="true">' if brace else "<staffGrp>"
    return ('<?xml version="1.0" encoding="UTF-8"?><mei xmlns="http://www.music-encoding.org/ns/mei" meiversion="4.0.0">'
            "<meiHead><fileDesc><titleStmt><title/></titleStmt><pubStmt/></fileDesc></meiHead><music><body><mdiv><score>"
            f"<scoreDef>{grp}{defs}</staffGrp></scoreDef><section>{body}</section></score></mdiv></body></music></mei>")


class Engraver:
    def __init__(self):
        import verovio
        self.tk = verovio.toolkit()

    def render(self, rng, mei):
        import cairosvg
        from PIL import Image
        self.tk.setOptions({"adjustPageHeight": True, "adjustPageWidth": True, "footer": "none", "header": "none",
                            "scale": rng.randint(45, 90), "font": rng.choice(["Leipzig", "Bravura", "Gootville", "Leland"]),
                            "pageMarginTop": 30, "pageMarginBottom": 30, "pageMarginLeft": 30, "pageMarginRight": 30,
                            "svgViewBox": False, "breaks": "none", "pageWidth": 6000})
        if not self.tk.loadData(mei):
            return None
        png = cairosvg.svg2png(bytestring=self.tk.renderToSVG(1).encode(), background_color="white")
        return Image.open(io.BytesIO(png))


def interval_of(lo, hi):
    """(number, quality) for two pitches, or None for qualities beyond dim/aug."""
    num = hi["d"] - lo["d"] + 1
    semis = p_semi(hi["step"], hi["acc"], hi["oct"]) - p_semi(lo["step"], lo["acc"], lo["oct"])
    simple = (num - 1) % 7 + 1
    s = semis - 12 * ((num - 1) // 7)
    if simple in (1, 4, 5):
        q = {0: "perfect", 1: "augmented", -1: "diminished"}.get(s - {1: 0, 4: 5, 5: 7}[simple])
    else:
        q = {0: "major", -1: "minor", 1: "augmented", -2: "diminished"}.get(s - {2: 2, 3: 4, 6: 9, 7: 11}[simple])
    if q is None or (num == 1 and q != "perfect") or semis < 0:
        return None
    return num, q, semis


def nth(n):
    return {1: "unison", 8: "octave"}.get(n, f"{n}{'th' if 4 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}")


def art(word):
    return "an" if word[0] in "aeiou" else "a"


def interval_name(num, q):
    if num <= 8:
        return f"{q} {nth(num)}"
    return f"{q} {nth(num)} (compound {q} {nth(num - 7)})"


def m_note_name(rng, clef_pool):
    clef = rng.choice(clef_pool)
    key = rng.choice([0] * 6 + [1, 2, 3, -1, -2, -3])
    n = rand_note(rng, clef, key=key)
    ans = p_name(n["step"], n["acc"])
    wrong = {p_name((n["step"] + k) % 7, n["acc"]) for k in (1, 2, 3, 4, 5, 6)}
    if n["acc"]:
        wrong.add(STEPS[n["step"]])
    opts = [ans] + rng.sample(sorted(wrong), 3)
    q = rng.choice(["Select the name of this note.", "What is the letter name of the note shown?", "Name the note."])
    sol = (f"The staff has {art(CLEFS[clef][3])} {CLEFS[clef][3]}: {CLEFS[clef][4]}. It has {key_text(key)}. "
           f"Counting lines and spaces from there, {read_text(n, clef)}. The note name is {ans}.")
    return mei_doc([(clef, [[note_xml(n)]])], key), "note_name", q, sol, ans, opts, False


def two_notes(rng, clef, key=0):
    for _ in range(50):
        a, b = rand_note(rng, clef, key=key, p_acc=0.35), rand_note(rng, clef, key=key, p_acc=0.35)
        lo, hi = sorted((a, b), key=lambda n: n["d"])
        if not 1 <= hi["d"] - lo["d"] <= 12:
            continue
        iv = interval_of(lo, hi)
        if iv and iv[1] in ("augmented", "diminished") and (iv[0] - 1) % 7 + 1 not in (4, 5) and rng.random() < 0.85:
            continue  # augmented 3rds, diminished 6ths ... exist but are rare in practice
        if iv:
            return lo, hi, iv
    return None


def m_interval(rng, clef_pool):
    clef = rng.choice(clef_pool)
    key = rng.choice([0] * 5 + [1, 2, -1, -2])
    got = two_notes(rng, clef, key)
    if not got:
        return None
    lo, hi, (num, q, semis) = got
    stacked = rng.random() < 0.5 and hi["d"] - lo["d"] >= 2
    events = [chord_xml([lo, hi])] if stacked else ([note_xml(lo), note_xml(hi)] if rng.random() < 0.6 else [note_xml(hi), note_xml(lo)])
    letters = " ".join(STEPS[(lo["step"] + k) % 7] for k in range(min(num, 8))) + (" ..." if num > 8 else "")
    sol = (f"The staff has {art(CLEFS[clef][3])} {CLEFS[clef][3]}: {CLEFS[clef][4]}. It has {key_text(key)}. "
           f"Lower note: {read_text(lo, clef)}. Upper note: {read_text(hi, clef)}. "
           f"Counting letter names from {STEPS[lo['step']]} up to {STEPS[hi['step']]} ({letters}) gives a {nth(num)}"
           f"{' (an octave plus a ' + nth(num - 7) + ')' if num > 8 else ''}. "
           f"The distance is {semis} semitones, so the interval is {art(q)} {interval_name(num, q)}.")
    if rng.random() < 0.5:
        quals = ["perfect", "major", "minor", "diminished", "augmented"]
        opts = [q] + rng.sample([x for x in quals if x != q], 3)
        return (mei_doc([(clef, [events])], key), "interval_quality",
                rng.choice(["Select the type of the interval.", "What is the quality of this interval?"]), sol, q, opts, False)
    wrong = set()
    for dn in (-2, -1, 0, 1, 2):
        for qq in ("major", "minor", "perfect", "augmented", "diminished"):
            n2 = num + dn
            ok = (qq == "perfect") == ((n2 - 1) % 7 + 1 in (1, 4, 5)) or qq in ("augmented", "diminished")
            if n2 >= 2 and ok and (n2, qq) != (num, q):
                wrong.add(interval_name(n2, qq).split(" (")[0])
    ans = interval_name(num, q).split(" (")[0]
    opts = [ans] + rng.sample(sorted(wrong), 3)
    return mei_doc([(clef, [events])], key), "interval_name", rng.choice(["Name the interval.", "Describe the interval fully."]), sol, ans, opts, False


def m_chord(rng, clef_pool):
    clef = rng.choice(clef_pool)
    for _ in range(100):
        qual = rng.choice(list(CHORDS))
        iv = CHORDS[qual]
        rs, ra = rng.randrange(7), rng.choice([0, 0, 0, 1, -1])
        ro = (CLEFS[clef][2] + rng.randint(-1, 4)) // 7
        tones = []
        for k, off in enumerate(iv):
            d = ro * 7 + rs + 2 * k
            step, octave = d % 7, d // 7
            acc = p_semi(rs, ra, ro) + off - p_semi(step, 0, octave)
            if abs(acc) > 1:
                break
            tones.append({"step": step, "oct": octave, "acc": acc, "shown": acc if acc else None, "d": d})
        else:
            inv = rng.randrange(len(iv))
            for t in tones[:inv]:
                t["oct"] += 1
                t["d"] += 7
            tones.sort(key=lambda t: t["d"])
            for t in tones:
                t["pos"] = t["d"] - CLEFS[clef][2]
            if -4 <= tones[0]["pos"] and tones[-1]["pos"] <= 12:
                break
    else:
        return None
    root = p_name(rs, ra)
    stack = ", ".join(p_name(t["step"], t["acc"], t["oct"]) for t in tones)
    thirds = " - ".join(p_name((rs + 2 * k) % 7, p_semi(rs, ra, 0) + off - p_semi((rs + 2 * k) % 7, 0, (rs + 2 * k) // 7))
                        for k, off in enumerate(iv))
    member = ["root", "third", "fifth", "seventh"][inv]
    ans = f"{qual[0].upper()}{qual[1:]} in {INVERSIONS[inv]}"
    sol = (f"The staff has {art(CLEFS[clef][3])} {CLEFS[clef][3]}: {CLEFS[clef][4]}. Reading the stacked notes from the bottom: {stack}. "
           f"Rearranged in thirds they are {thirds}, so the root is {root}. The intervals above the root are "
           f"{', '.join(str(x) for x in iv[1:])} semitones, which is {art(qual)} {qual}. "
           f"The lowest written note is the {member} of the chord, so it is in {INVERSIONS[inv]}.")
    wrong = set()
    while len(wrong) < 3:
        q2 = rng.choice([c for c in CHORDS if len(CHORDS[c]) == len(iv)])
        w = f"{q2[0].upper()}{q2[1:]} in {INVERSIONS[rng.randrange(len(iv))]}"
        if w != ans:
            wrong.add(w)
    q = rng.choice(["Which of the following best describes the chord?", "Identify the chord and its inversion."])
    return mei_doc([(clef, [[chord_xml(tones)]])]), "chord", q, sol, ans, [ans] + sorted(wrong), False


def major_scale(n):
    tonic = MAJOR_KEYS[n]
    s0 = STEPS.index(tonic[0])
    return [((s0 + k) % 7, key_acc((s0 + k) % 7, n)) for k in range(7)]


def m_degree(rng, clef_pool):
    clef = rng.choice(clef_pool)
    n = rng.randint(-4, 4)
    scale = major_scale(n)
    deg = rng.randrange(7)
    truth = rng.random() < 0.5
    if truth:
        step, acc = scale[deg]
    else:
        step, acc = scale[(deg + rng.choice([1, 2, 3, 4, 5, 6])) % 7] if rng.random() < 0.6 else (scale[deg][0], scale[deg][1] + rng.choice([-1, 1]))
        if abs(acc) > 1:
            return None
    cands = [d for d in range(CLEFS[clef][2] - 3, CLEFS[clef][2] + 12) if d % 7 == step]
    d = rng.choice(cands)
    note = {"step": step, "oct": d // 7, "acc": acc, "shown": acc if acc else None, "pos": d - CLEFS[clef][2], "d": d}
    key = MAJOR_KEYS[n]
    names = " ".join(p_name(*x) for x in scale)
    q = rng.choice([f"This is the {DEGREES[deg]} in {key} major.", f"True or False: this note is the {DEGREES[deg]} of {key} major."])
    sol = (f"The staff has {art(CLEFS[clef][3])} {CLEFS[clef][3]}: {CLEFS[clef][4]}. So {read_text(note, clef)}. "
           f"The {key} major scale is {names}; its {DEGREES[deg]} is the {nth(deg + 1) if deg else '1st'} degree, {p_name(*scale[deg])}. "
           f"The written note is {p_name(step, acc)}, so the statement is {'true' if truth else 'false'}.")
    return mei_doc([(clef, [[note_xml(note)]])]), "scale_degree", q, sol, str(truth), ["True", "False"], True


def m_keysig(rng, clef_pool):
    clef = rng.choice(clef_pool)
    n = rng.choice([x for x in range(-5, 6) if x])
    minor = rng.random() < 0.4
    table = MINOR_KEYS if minor else MAJOR_KEYS
    ans = f"{table[n]} {'minor' if minor else 'major'}"
    wrong = [f"{table[k]} {'minor' if minor else 'major'}" for k in table if k != n]
    note = rand_note(rng, clef, lo=0, hi=8, key=n, p_acc=0)
    q = f"Which {'minor' if minor else 'major'} key has this key signature?"
    sol = (f"The staff shows {key_text(n)}. "
           + (f"With sharps, the major key is a semitone above the last sharp ({SHARP_ORDER[n - 1]}#): {MAJOR_KEYS[n]} major. " if n > 0 else
              f"With flats, the major key is {'F' if n == -1 else 'the second-to-last flat'}: {MAJOR_KEYS[n]} major. ")
           + (f"Its relative minor, a minor third lower, is {MINOR_KEYS[n]} minor." if minor else ""))
    return mei_doc([(clef, [[note_xml(note)]])], n), "key_signature", q, sol, ans, [ans] + rng.sample(wrong, 3), False


UNITS = [(1, 0, 16), (2, 1, 12), (2, 0, 8), (4, 1, 6), (4, 0, 4), (8, 1, 3), (8, 0, 2), (16, 0, 1)]  # dur, dots, sixteenths


def fill(rng, total, clef, key, rests=0.15):
    ev, left = [], total
    while left > 0:
        dur, dots, n16 = rng.choice([u for u in UNITS if u[2] <= left and u[2] <= 8 or u[2] == left])
        if rng.random() < rests:
            ev.append((f'<rest dur="{dur}"{" dots=" + chr(34) + str(dots) + chr(34) if dots else ""}/>', dur, dots, n16, True))
        else:
            ev.append((note_xml(rand_note(rng, clef, lo=0, hi=9, key=key, p_acc=0.08), dur, dots), dur, dots, n16, False))
        left -= n16
    return ev


def m_bars(rng, clef_pool):
    clef = rng.choice(clef_pool[:2])
    meter = rng.choice([(2, 4), (3, 4), (4, 4), (6, 8), (3, 8)])
    key = rng.choice([0, 0, 1, -1, 2, -2])
    n = rng.randint(3, 9)
    per = meter[0] * (16 // meter[1])
    meas = [[e[0] for e in fill(rng, per, clef, key)] for _ in range(n)]
    q = rng.choice(["How many measures (bars) are in this excerpt?",
                    "Based on the time signature, the number of measures/bars in this music is _____."])
    sol = (f"The time signature is {meter[0]}/{meter[1]}, so every measure holds {meter[0]} "
           f"{DUR_NAME[meter[1]]}-note beats. Counting the groups separated by bar lines, up to the final double bar, gives {n} measures.")
    opts = [n] + rng.sample([x for x in range(max(2, n - 3), n + 4) if x != n], 3) if rng.random() < 0.7 else None
    return mei_doc([(clef, meas)], key, meter), "bar_count", q, sol, n, opts, False


def dur_words(e):
    return f"{'dotted ' if e[2] else ''}{DUR_NAME[e[1]]} {'rest' if e[4] else 'note'} = {e[3] / 4:g}"


def m_meter(rng, clef_pool):
    clef = rng.choice(clef_pool[:2])
    meters = {"2/4": 8, "3/4": 12, "4/4": 16, "5/4": 20, "9/8": 18, "7/8": 14}
    ans = rng.choice(list(meters))
    ev = fill(rng, meters[ans], clef, 0)
    q = "The time signature has been left out. Which time signature fits this complete bar?"
    sol = ("Adding the values in quarter-note beats: " + ", ".join(dur_words(e) for e in ev)
           + f". The total is {meters[ans] / 4:g} quarter-note beats ({meters[ans] // 2} eighth notes), which fills one bar of {ans}.")
    return mei_doc([(clef, [[e[0] for e in ev]])]), "time_signature", q, sol, ans, [ans] + rng.sample([m for m in meters if m != ans], 3), False


def m_duration(rng, clef_pool):
    clef = rng.choice(clef_pool[:2])
    total = rng.choice([4, 5, 6, 7, 9, 10, 11, 12, 14])
    ev = fill(rng, total, clef, 0, rests=rng.choice([0.2, 1.0]))
    if len(ev) < 2:
        return None
    q = rng.choice(["What is the total duration of the notes and rests shown, in quarter-note beats?",
                    "How many quarter-note beats do these values add up to?"])
    sol = "In quarter-note beats: " + ", ".join(dur_words(e) for e in ev) + f". The sum is {total / 4:g}."
    ans = f"{total / 4:g}"
    opts = [ans] + [f"{x / 4:g}" for x in rng.sample([t for t in range(max(2, total - 4), total + 5) if t != total], 3)] if rng.random() < 0.5 else None
    return mei_doc([(clef, [[e[0] for e in ev]])]), "duration_sum", q, sol, ans, opts, False


MUSIC_TASKS = [(m_note_name, 5), (m_interval, 6), (m_chord, 4), (m_degree, 3), (m_keysig, 2), (m_bars, 2), (m_meter, 2), (m_duration, 2)]


def gen_music(rng, n, img_dir):
    eng = Engraver()
    out, i = [], 0
    funcs = [f for f, w in MUSIC_TASKS for _ in range(w)]
    while len(out) < n:
        i += 1
        got = rng.choice(funcs)(rng, ["treble", "bass", "treble", "bass", "alto", "tenor"])
        if not got:
            continue
        mei, kind, q, sol, ans, opts, fixed = got
        img = eng.render(rng, mei)
        if img is None:
            continue
        rec = record(rng, f"percept::music::{kind}::{i}", "percept_music", kind, q, sol, ans, opts, fixed)
        if rec:
            path = img_dir / f"music_{i}.png"
            scan_like(rng, img).save(path)
            rec["images"] = [str(path)]
            out.append(rec)
    return out


# ----------------------------------------------------------------------------- chemistry
def load_smiles(smiles_dir):
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    seen, mols = set(), []
    for name, col in (("BBBP.csv", "smiles"), ("delaney-processed.csv", "smiles")):
        p = Path(smiles_dir) / name
        if not p.exists():
            continue
        for row in csv.DictReader(open(p, encoding="utf-8", errors="ignore")):
            smi = max((row.get(col) or "").split("."), key=len)
            m = Chem.MolFromSmiles(smi) if smi else None
            if m is None or not 6 <= m.GetNumHeavyAtoms() <= 32:
                continue
            can = Chem.MolToSmiles(m)
            if can not in seen and all(a.GetSymbol() in ("C", "N", "O", "S", "F", "Cl", "Br", "I", "P") for a in m.GetAtoms()):
                seen.add(can)
                mols.append(can)
    return mols


def draw_mol(rng, mol, highlight=None, size=None):
    from PIL import Image
    from rdkit.Chem.Draw import rdMolDraw2D
    w = size or rng.randint(260, 460)
    d = rdMolDraw2D.MolDraw2DCairo(w, int(w * rng.uniform(0.75, 1.0)))
    o = d.drawOptions()
    o.rotate = rng.uniform(0, 360)
    o.bondLineWidth = rng.choice([1, 2, 2, 3])
    if rng.random() < 0.8:
        o.useBWAtomPalette()
    rdMolDraw2D.PrepareAndDrawMolecule(d, mol, highlightAtoms=highlight or [])
    d.FinishDrawing()
    return Image.open(io.BytesIO(d.GetDrawingText()))


def centres(mol):
    from rdkit import Chem
    return Chem.FindMolChiralCenters(mol, includeUnassigned=True, useLegacyImplementation=False)


def atom_text(a):
    nb = sorted(n.GetSymbol() for n in a.GetNeighbors()) + ["H"] * a.GetTotalNumHs()
    return f"the {a.GetSymbol()} bonded to {', '.join(nb)}"


def c_count(rng, smi):
    from rdkit import Chem
    m = Chem.MolFromSmiles(smi)
    cs = centres(m)
    if len(cs) > 7 or any(lab == "?" for _, lab in cs):
        return None
    n = len(cs)
    q = rng.choice(["How many chirality centers does this molecule have?", "How many stereocenters (chiral centers) are in the structure shown?"])
    if n:
        sol = ("A chirality center is an sp3 atom with four different groups. Going through the structure, these atoms qualify: "
               + "; ".join(atom_text(m.GetAtomWithIdx(i)) for i, _ in cs) + f". All other atoms have two identical groups or a double bond. That gives {n}.")
    else:
        sol = "A chirality center is an sp3 atom with four different groups. Every sp3 atom here carries at least two identical groups (or the atom is sp2), so there is none: 0."
    opts = [n] + rng.sample([x for x in range(0, n + 4) if x != n], 3) if rng.random() < 0.5 else None
    return draw_mol(rng, m), "stereocenter_count", q, sol, n, opts, False


def c_rs(rng, smi):
    from rdkit import Chem
    m = Chem.MolFromSmiles(smi)
    cs = [(i, lab) for i, lab in centres(m) if lab in ("R", "S") and m.GetAtomWithIdx(i).GetSymbol() == "C"]
    if not cs or len(centres(m)) > 5:
        return None
    Chem.AssignStereochemistry(m, cleanIt=True, force=True)
    i, lab = rng.choice(cs)
    a = m.GetAtomWithIdx(i)
    nbs = sorted(a.GetNeighbors(), key=lambda x: -int(x.GetProp("_CIPRank")))
    order = " > ".join(f"{x.GetSymbol()}{'(' + ''.join(sorted(y.GetSymbol() for y in x.GetNeighbors() if y.GetIdx() != i)) + ')' if x.GetDegree() > 1 else ''}" for x in nbs)
    if a.GetTotalNumHs():
        order += " > H"
    q = "What is the configuration (R or S) of the highlighted stereocenter?"
    sol = (f"The highlighted atom is {atom_text(a)}. CIP priorities of its substituents (attached atom, then the atoms on it): {order}. "
           f"With the lowest-priority group pointing away from the viewer, going from priority 1 to 2 to 3 is "
           f"{'clockwise' if lab == 'R' else 'counter-clockwise'}, so the configuration is {lab}.")
    return draw_mol(rng, m, highlight=[i]), "r_or_s", q, sol, lab, ["R", "S"], True


def c_isomers(rng, smi):
    from rdkit import Chem
    from rdkit.Chem.EnumerateStereoisomers import EnumerateStereoisomers, StereoEnumerationOptions
    m = Chem.MolFromSmiles(smi)
    Chem.RemoveStereochemistry(m)
    info = Chem.FindPotentialStereo(m)
    nc = sum(1 for x in info if x.type == Chem.StereoType.Atom_Tetrahedral)
    nd = sum(1 for x in info if x.type == Chem.StereoType.Bond_Double)
    ring = m.GetRingInfo()
    if not 1 <= nc + nd <= 5 or any(x.type == Chem.StereoType.Atom_Tetrahedral and ring.NumAtomRings(x.centeredOn) > 1 for x in info):
        return None  # ring-fusion / bridgehead centres cannot all be inverted independently
    k = len(list(EnumerateStereoisomers(m, options=StereoEnumerationOptions(unique=True, onlyUnassigned=False, maxIsomers=64))))
    full = 2 ** (nc + nd)
    q = rng.choice(["What is the maximum number of stereoisomers that could exist for this compound?", "How many stereoisomers are possible for the structure shown?"])
    sol = (f"The structure has {nc} stereocenter{'s' if nc != 1 else ''} and {nd} double bond{'s' if nd != 1 else ''} that can be E or Z, "
           f"so n = {nc + nd} and 2^n = {full}." + (f" Because of the molecule's symmetry some of these are identical (meso forms), leaving {k}." if k < full else ""))
    opts = [k] + rng.sample([x for x in {1, 2, 3, 4, 6, 8, 10, 12, 16, 32, full, max(1, k // 2), k * 2} if x != k], 3) if rng.random() < 0.6 else None
    return draw_mol(rng, m), "stereoisomer_count", q, sol, k, opts, False


def c_pair(rng, smi):
    from PIL import Image, ImageDraw
    from rdkit import Chem
    a = Chem.MolFromSmiles(smi)
    cs = [i for i, lab in centres(a) if lab in ("R", "S")]
    if not 1 <= len(cs) <= 4 or len(cs) != len(centres(a)):
        return None
    b = Chem.Mol(a)
    mode = rng.choice(["same", "mirror", "some"])
    flip = [] if mode == "same" else cs if mode == "mirror" else rng.sample(cs, rng.randint(1, max(1, len(cs) - 1)))
    for i in flip:
        b.GetAtomWithIdx(i).InvertChirality()
    mir = Chem.Mol(a)
    for i in cs:
        mir.GetAtomWithIdx(i).InvertChirality()
    sa, sb, sm = (Chem.MolToSmiles(x) for x in (a, b, mir))
    ans = "identical (the same compound)" if sa == sb else "enantiomers" if sb == sm else "diastereomers"
    ia, ib = draw_mol(rng, a, size=320), draw_mol(rng, Chem.MolFromSmiles(sb), size=320)
    img = Image.new("RGB", (ia.width + ib.width + 30, max(ia.height, ib.height) + 30), "white")
    img.paste(ia, (0, 0))
    img.paste(ib, (ia.width + 30, 0))
    dr = ImageDraw.Draw(img)
    from PIL import ImageFont
    font = ImageFont.load_default(size=22)
    dr.text((ia.width // 2, img.height - 30), "I", fill="black", font=font)
    dr.text((ia.width + 30 + ib.width // 2, img.height - 30), "II", fill="black", font=font)
    Chem.AssignStereochemistry(a, cleanIt=True, force=True)
    bb = Chem.MolFromSmiles(sb)
    la = "".join(lab for _, lab in centres(a))
    lb = "".join(lab for _, lab in centres(Chem.RenumberAtoms(b, list(range(b.GetNumAtoms())))))
    n_diff = len(flip)
    sol = (f"Both drawings have the same atoms and the same connectivity with {len(cs)} stereocenter{'s' if len(cs) > 1 else ''}; only the wedge/dash "
           f"bonds can differ. Assigning each center: compound I is {','.join(la)} and compound II is {','.join(lb)} for the corresponding atoms. "
           + ("Every center has the same configuration, so the two drawings show the same compound, only rotated on the page."
              if ans.startswith("identical") and n_diff == 0 else
              "Every center is inverted but the molecule has an internal mirror plane (meso), so both drawings are the same compound."
              if ans.startswith("identical") else
              "Every center is inverted, so they are non-superimposable mirror images: enantiomers." if ans == "enantiomers" else
              "Some but not all centers differ, so they are stereoisomers that are not mirror images: diastereomers."))
    q = "What is the relationship between compounds I and II?"
    return img, "stereo_pair", q, sol, ans, ["identical (the same compound)", "enantiomers", "diastereomers", "constitutional isomers"], False


def c_formula(rng, smi):
    from rdkit import Chem
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    m = Chem.MolFromSmiles(smi)
    if m.GetNumHeavyAtoms() > 22 or Chem.GetFormalCharge(m):
        return None
    cnt = Counter(a.GetSymbol() for a in m.GetAtoms())
    h = sum(a.GetTotalNumHs() for a in m.GetAtoms())
    ans = CalcMolFormula(m)

    def fm(c, hh):
        rest = "".join(f"{k}{v if v > 1 else ''}" for k, v in sorted(cnt.items()) if k != "C")
        return f"C{c if c > 1 else ''}H{hh if hh > 1 else ''}{rest}"
    if fm(cnt["C"], h) != ans:
        return None
    wrong = {fm(cnt["C"], h + 2), fm(cnt["C"], max(1, h - 2)), fm(cnt["C"] + 1, h + 2), fm(max(1, cnt["C"] - 1), max(1, h - 2)), fm(cnt["C"], h + 1)} - {ans}
    hetero = ", ".join(f"{v} {k}" for k, v in sorted(cnt.items()) if k != "C") or "no heteroatoms"
    sol = (f"In a skeletal formula every line end and corner is a carbon: {cnt['C']} C. Labelled heteroatoms: {hetero}. "
           f"Each carbon carries enough hydrogens to reach four bonds; adding those to the hydrogens written on heteroatoms gives {h} H. The formula is {ans}.")
    return draw_mol(rng, m), "formula", "What is the molecular formula of the compound shown?", sol, ans, [ans] + rng.sample(sorted(wrong), 3), False


CHEM_TASKS = [(c_count, 4), (c_rs, 3), (c_isomers, 3), (c_pair, 3), (c_formula, 2)]


def gen_chem(rng, n, img_dir, smiles_dir):
    from rdkit import Chem
    pool = load_smiles(smiles_dir)
    chiral = [s for s in pool if "@" in s]
    funcs = [f for f, w in CHEM_TASKS for _ in range(w)]
    out, i = [], 0
    while len(out) < n and i < n * 60:
        i += 1
        f = rng.choice(funcs)
        smi = rng.choice(pool if f in (c_formula, c_isomers) or (f is c_count and rng.random() < 0.25) else chiral)
        try:
            got = f(rng, smi)
        except Exception:
            got = None
        if not got:
            continue
        img, kind, q, sol, ans, opts, fixed = got
        rec = record(rng, f"percept::chem::{kind}::{i}", "percept_chem", kind, q, sol, ans, opts, fixed)
        if rec:
            path = img_dir / f"chem_{i}.png"
            scan_like(rng, img, strength=0.6).save(path)
            rec["images"] = [str(path)]
            out.append(rec)
    return out


# ----------------------------------------------------------------------------- plots
def fig_image(fig):
    import matplotlib.pyplot as plt
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return Image.open(io.BytesIO(buf.getvalue()))


def new_fig(rng):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = rng.choice(["DejaVu Sans", "DejaVu Serif"])
    fig, ax = plt.subplots(figsize=(rng.uniform(4, 5.5), rng.uniform(3.2, 4.2)), dpi=rng.choice([80, 100, 120]))
    return fig, ax


def p_phase(rng):
    import numpy as np
    tt, pt = rng.uniform(0.3, 0.45), rng.uniform(0.25, 0.4)
    tc, pc = rng.uniform(0.8, 0.92), rng.uniform(0.7, 0.9)
    slope = rng.choice([-1, 1]) * rng.uniform(0.04, 0.12)  # dT/dP of the solid-liquid line (negative = water-like)
    k = math.log(pc / pt) / (tc - tt)
    p_lg = lambda t: pt * math.exp(k * (t - tt))
    p_sg = lambda t: pt * (t / tt) ** 2.2
    t_sl = lambda p: tt + slope * (p - pt)

    def phase(t, p, eps=0.045):
        if p > pt:
            if abs(t - t_sl(p)) < eps or (t > t_sl(p) and t < tc and abs(p - p_lg(t)) < eps):
                return None
            return "solid" if t < t_sl(p) else "liquid" if (t >= tc or p > p_lg(t)) and t < tc else "gas" if t < tc else None
        if t < tt:
            return None if abs(p - p_sg(t)) < eps else "solid" if p > p_sg(t) else "gas"
        return None if abs(p - p_lg(min(t, tc))) < eps and t < tc else "gas"

    pts = {}
    for _ in range(400):
        t, p = rng.uniform(0.08, 0.78), rng.uniform(0.08, 0.95)
        ph = phase(t, p)
        if ph and sum(v[2] == ph for v in pts.values()) < 2 and all(abs(t - v[0]) + abs(p - v[1]) > 0.14 for v in pts.values()):
            pts[len(pts)] = (t, p, ph)
        if len(pts) >= 5:
            break
    lines = [("solid-liquid line (melting/freezing)", (t_sl(pt + (1 - pt) * 0.55), pt + (1 - pt) * 0.55)),
             ("liquid-gas line (boiling/condensation)", ((tt + tc) / 2, p_lg((tt + tc) / 2))),
             ("solid-gas line (sublimation/deposition)", (tt * 0.6, p_sg(tt * 0.6))),
             ("triple point", (tt, pt))]
    for name, (t, p) in rng.sample(lines, rng.randint(1, 3)):
        pts[len(pts)] = (t, p, name)
    if len({v[2] for v in pts.values()}) < 3:
        return None
    labels = rng.choice([list("ABCDEFGHI"), list("123456789"), list("PQRSTUVWX")])
    order = list(pts.values())
    rng.shuffle(order)
    fig, ax = new_fig(rng)
    ts = np.linspace(0.04, tt, 40)
    ax.plot(ts, [p_sg(t) for t in ts], "k")
    ts = np.linspace(tt, tc, 40)
    ax.plot(ts, [p_lg(t) for t in ts], "k")
    ps = np.linspace(pt, 1.0, 10)
    ax.plot([t_sl(p) for p in ps], ps, "k")
    for lab, (t, p, _) in zip(labels, order):
        ax.plot(t, p, "ko", ms=4)
        ax.annotate(lab, (t, p), textcoords="offset points", xytext=(6, 5), fontsize=11)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(rng.choice(["Temperature", "Temperature (°C)", "T"]))
    ax.set_ylabel(rng.choice(["Pressure", "Pressure (atm)", "P"]))
    target = rng.choice(order)
    others = [lab for lab, v in zip(labels, order) if v[2] != target[2]]
    ans = labels[order.index(target)]
    same = [lab for lab, v in zip(labels, order) if v[2] == target[2]]
    if len(same) > 1 or len(others) < 3:
        return None
    if target[2] in ("solid", "liquid", "gas"):
        q = f"At which labeled point is the substance only in the {target[2]} phase at equilibrium?"
    elif target[2] == "triple point":
        q = "Which labeled point is the triple point?"
    else:
        pair, what = target[2].split(" line ")
        q = f"Which labeled point lies on the {pair} equilibrium line {what}?"
    desc = "; ".join(f"{lab} is {('on the ' + v[2]) if 'line' in v[2] else ('at the ' + v[2]) if v[2] == 'triple point' else ('in the ' + v[2] + ' region')}"
                     for lab, v in zip(labels, order))
    sol = ("Three curves meet at the triple point. The region at low temperature and high pressure (left of the steep line) is solid, "
           "the region between the steep line and the curve rising to the right is liquid, and the region at low pressure / high temperature "
           f"below the curves is gas. A point on a curve has two phases in equilibrium. Placing each point: {desc}. So the answer is {ans}.")
    return fig_image(fig), "phase_diagram", q, sol, ans, [ans] + rng.sample(others, 3), False


def titration_ph(v, veq, c0, v0, weak, acid_analyte, pk):
    """pH after adding v mL of strong titrant to a monoprotic analyte (charge balance, bisection)."""
    n0, tot = c0 * v0, v0 + v
    ct = c0 * v0 / veq  # titrant concentration
    ca, cb = n0 / tot, ct * v / tot
    k = 10 ** -pk if weak else 1e6

    def f(ph):  # for an acid analyte + strong base: [H] + [Na] - [OH] - [A-]
        h = 10 ** -ph
        return h + cb - 1e-14 / h - ca * k / (k + h)
    lo, hi = 0.0, 14.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    ph = (lo + hi) / 2
    return ph if acid_analyte else 14 - ph


def p_titration(rng):
    import numpy as np
    kinds = {"a strong base is titrated into a strong acid": (False, True), "a strong base is titrated into a weak acid": (True, True),
             "a strong acid is titrated into a strong base": (False, False), "a strong acid is titrated into a weak base": (True, False)}
    name = rng.choice(list(kinds))
    weak, acid = kinds[name]
    veq = rng.choice([10, 12.5, 15, 20, 25, 30, 40])
    c0, v0, pk = rng.choice([0.05, 0.1, 0.2]), 25.0, rng.uniform(4.2, 5.4)
    vmax = veq * rng.uniform(1.5, 2.0)
    vs = np.linspace(0, vmax, 400)
    phs = [titration_ph(v, veq, c0, v0, weak, acid, pk) for v in vs]
    fig, ax = new_fig(rng)
    ax.plot(vs, phs, "k")
    ax.set_xlim(0, vmax)
    ax.set_ylim(0, 14)
    ax.set_yticks(range(0, 15, 2))
    if rng.random() < 0.6:
        ax.grid(alpha=0.4)
    ax.set_xlabel(f"Volume of titrant added (mL)")
    ax.set_ylabel("pH")
    ph0, pheq = phs[0], titration_ph(veq, veq, c0, v0, weak, acid, pk)
    start = f"The curve starts at a {'low' if acid else 'high'} pH (about {ph0:.1f}), so the solution in the flask is {'an acid' if acid else 'a base'} and the titrant is a strong {'base' if acid else 'acid'}."
    eq = (f" The steep jump is centred near {veq:g} mL, where the pH is about {pheq:.1f}; "
          + (f"an equivalence point {'above' if acid else 'below'} 7{' and a gently sloping buffer region before it' } means the analyte is weak."
             if weak else "an equivalence point at pH 7 means the analyte is strong."))
    mode = rng.choice(["type", "type", "veq", "pheq"])
    if mode == "type":
        q = rng.choice(["Which of the following matches the titration curve shown?", "Which titration does this curve represent?"])
        opts = [n[0].upper() + n[1:] + "." for n in kinds]
        return fig_image(fig), "titration_type", q, start + eq + f" So {name}.", name[0].upper() + name[1:] + ".", opts, False
    if mode == "veq":
        q = "What volume of titrant has been added at the equivalence point (in mL)?"
        sol = start + f" The equivalence point is the middle of the nearly vertical section, at about {veq:g} mL."
        opts = [f"{veq:g}"] + [f"{x:g}" for x in rng.sample([v for v in (5, 10, 12.5, 15, 20, 25, 30, 40, 50) if v != veq], 3)]
        return fig_image(fig), "titration_veq", q, sol, f"{veq:g}", opts, False
    q = "Is the pH at the equivalence point less than 7, equal to 7, or greater than 7?"
    ans = "equal to 7" if not weak else "greater than 7" if acid else "less than 7"
    return fig_image(fig), "titration_pheq", q, start + eq, ans, ["less than 7", "equal to 7", "greater than 7"], True


def p_calibration(rng):
    import numpy as np
    slope = rng.choice([20, 25, 40, 50, 60, 80])
    xmax = rng.choice([0.01, 0.015, 0.02])
    xs = np.linspace(xmax / 5, xmax, 5)
    ys = [slope * x * (1 + rng.uniform(-0.03, 0.03)) for x in xs]
    fig, ax = new_fig(rng)
    ax.plot(xs, ys, "ko", ms=4)
    ax.plot([0, xmax * 1.05], [0, slope * xmax * 1.05], "k", lw=1)
    ax.set_xlim(0, xmax * 1.1)
    ax.set_ylim(0, slope * xmax * 1.15)
    ax.grid(True, alpha=0.5)
    ax.locator_params(axis="x", nbins=5)
    ax.set_xlabel("Concentration (M)")
    ax.set_ylabel("Absorbance")
    a = round(rng.uniform(0.25, 0.9) * slope * xmax, 2)
    conc = a / slope
    vol = rng.choice([25.0, 50.0, 100.0, 250.0])
    if rng.random() < 0.5:
        q = f"The calibration plot above was made with solutions of known concentration. A sample has an absorbance of {a:.2f}. What is its concentration in mol/L?"
        sol = (f"The line passes through the origin and through about ({xmax:g} M, {slope * xmax:.2f}), so its slope is {slope} per M. "
               f"Concentration = absorbance / slope = {a:.2f} / {slope} = {conc:.4f} M.")
        return fig_image(fig), "calibration_conc", q, sol, f"{conc:.4f}", None, False
    mol = conc * vol / 1000
    q = (f"A sample solution with a total volume of {vol:g} mL has an absorbance of {a:.2f}. Using the calibration plot, "
         "how many moles of the absorbing species does the solution contain? Give the number in units of 10^-4 mol.")
    sol = (f"The line passes through the origin and about ({xmax:g} M, {slope * xmax:.2f}): slope {slope} per M. "
           f"Concentration = {a:.2f} / {slope} = {conc:.4f} M. Moles = {conc:.4f} mol/L x {vol / 1000:g} L = {mol:.2e} mol = {mol * 1e4:.2f} x 10^-4 mol.")
    return fig_image(fig), "calibration_moles", q, sol, f"{mol * 1e4:.2f}", None, False


def p_table(rng):
    sym = rng.choice(["X", "Q", "Z", "E", "M"])
    base = rng.randint(20, 120)
    k = rng.choice([2, 3, 3, 4])
    masses = sorted(rng.sample(range(base, base + 7), k))
    cuts = sorted(rng.sample(range(5, 96), k - 1))
    ab = [b - a for a, b in zip([0] + cuts, cuts + [100])]
    exact = [m - rng.uniform(0.01, 0.09) for m in masses] if rng.random() < 0.5 else [float(m) for m in masses]
    avg = sum(m * a for m, a in zip(exact, ab)) / 100
    fig, ax = new_fig(rng)
    ax.axis("off")
    rows = [[f"{sym}-{m}", f"{e:.2f}" if e != int(e) else f"{e:.1f}", f"{a:.1f}%"] for m, e, a in zip(masses, exact, ab)]
    t = ax.table(cellText=rows, colLabels=["Isotope", "Mass (amu)", "Abundance (%)"], loc="center", cellLoc="center")
    t.scale(1, rng.uniform(1.4, 2.0))
    t.auto_set_font_size(False)
    t.set_fontsize(rng.choice([10, 11, 12]))
    q = f"The table lists the naturally occurring isotopes of a hypothetical element {sym}. Calculate its average atomic mass in amu, to two decimal places."
    terms = " + ".join(f"{r[1]} x {a / 100:.3f}" for r, a in zip(rows, ab))
    sol = f"Reading the table row by row and weighting each mass by its fractional abundance: {terms} = {avg:.2f} amu."
    return fig_image(fig), "table_average", q, sol, f"{avg:.2f}", None, False


PLOT_TASKS = [(p_phase, 4), (p_titration, 4), (p_calibration, 2), (p_table, 2)]


def gen_plot(rng, n, img_dir):
    funcs = [f for f, w in PLOT_TASKS for _ in range(w)]
    out, i = [], 0
    while len(out) < n:
        i += 1
        got = rng.choice(funcs)(rng)
        if not got:
            continue
        img, kind, q, sol, ans, opts, fixed = got
        rec = record(rng, f"percept::plot::{kind}::{i}", "percept_plot", kind, q, sol, ans, opts, fixed)
        if rec:
            path = img_dir / f"plot_{i}.png"
            scan_like(rng, img, strength=0.8).save(path)
            rec["images"] = [str(path)]
            out.append(rec)
    return out


# ----------------------------------------------------------------------------- main
def image_check(records, cache, max_bits):
    """dHash of every generated image against all MMMU images (cache from build_official_sft.py)."""
    import numpy as np
    from build_official_sft import dhash_bits
    if not Path(cache).exists():
        return records, {"image_check": "skipped (no MMMU hash cache; run build_official_sft.py --mfr_dir first)"}
    z = np.load(cache, allow_pickle=True)
    bench, ids = z["hashes"], list(z["ids"])
    pop = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint16)
    keep, flagged, mn = [], {}, 999
    for r in records:
        d = pop[np.bitwise_xor(bench, dhash_bits(r["images"][0])[None, :])].sum(1)
        k = int(d.argmin())
        mn = min(mn, int(d[k]))
        if d[k] <= max_bits:
            flagged[r["id"]] = {"bits": int(d[k]), "match": str(ids[k])}
        else:
            keep.append(r)
    return keep, {"benchmark_images": len(ids), "checked": len(records), "min_image_distance_bits": mn, "n_flagged": len(flagged), "flagged": flagged}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--n_music", type=int, default=3000)
    ap.add_argument("--n_chem", type=int, default=2000)
    ap.add_argument("--n_plot", type=int, default=1500)
    ap.add_argument("--smiles_dir", default=f"/data/{USER}/train_data/smiles")
    ap.add_argument("--hash_cache", default=f"/data/{USER}/train_data/mmmu_all_dhash.npz")
    ap.add_argument("--max_bits", type=int, default=10)
    ap.add_argument("--n_val", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out_dir)
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    records = gen_music(rng, a.n_music, img_dir) + gen_chem(rng, a.n_chem, img_dir, a.smiles_dir) + gen_plot(rng, a.n_plot, img_dir)
    records, report = image_check(records, a.hash_cache, a.max_bits)
    json.dump(report, open(out / "contamination_report.json", "w"), indent=1)
    rng.shuffle(records)
    val, train, nv = [], [], Counter()
    for r in records:
        if nv[r["src"]] < a.n_val:
            nv[r["src"]] += 1
            val.append(r)
        else:
            train.append(r)
    for name, rows in (("train", train), ("val", val)):
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats = {"train": dict(Counter(r["src"] for r in train)), "val": dict(nv), "train_total": len(train),
             "kinds": dict(sorted(Counter(f"{r['src']}/{r['kind']}" for r in train).items())),
             "contamination_flagged": report.get("n_flagged"), "min_image_distance_bits": report.get("min_image_distance_bits")}
    json.dump(stats, open(out / "build_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
