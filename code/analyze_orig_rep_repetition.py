import json
import argparse
import re
from collections import Counter
from statistics import mean, median


def load_jsonl(path):
    data = {}

    with open(path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            data[item["id"]] = item

    return data


def tokenize(text):
    """
    반복 분석용 간단한 토큰화.
    모델 tokenizer가 아니라 단어/숫자/문장부호 단위.
    """
    if text is None:
        return []

    text = str(text).lower()

    return re.findall(
        r"\w+|[^\w\s]",
        text
    )


def repetition_stats(text, n=3):
    """
    n-gram 반복 정도를 계산한다.

    repetition_count:
        동일한 n-gram이 반복된 추가 등장 횟수

    repetition_rate:
        전체 n-gram 중 반복된 추가 등장 비율
    """

    tokens = tokenize(text)

    if len(tokens) < n:
        return {
            "total": 0,
            "unique": 0,
            "repeated": 0,
            "rate": 0.0,
        }

    ngrams = [
        tuple(tokens[i:i+n])
        for i in range(len(tokens) - n + 1)
    ]

    counts = Counter(ngrams)

    repetition_count = sum(
        count - 1
        for count in counts.values()
        if count > 1
    )

    return {
        "total": len(ngrams),
        "unique": len(counts),
        "repeated": repetition_count,
        "rate": (
            repetition_count / len(ngrams)
            if ngrams
            else 0.0
        ),
    }


def classify_transition(orig, rep):
    orig_correct = orig.get("correct") is True
    rep_correct = rep.get("correct") is True

    if orig_correct and rep_correct:
        return "CC"

    if orig_correct and not rep_correct:
        return "CW"

    if not orig_correct and rep_correct:
        return "WC"

    return "WW"


def print_group(name, samples):
    if not samples:
        print(f"{name:<10} N=0")
        return

    orig_rates = [x["orig_rate"] for x in samples]
    rep_rates = [x["rep_rate"] for x in samples]

    changes = [
        x["rep_rate"] - x["orig_rate"]
        for x in samples
    ]

    reduced = sum(
        x < 0
        for x in changes
    )

    increased = sum(
        x > 0
        for x in changes
    )

    unchanged = sum(
        x == 0
        for x in changes
    )

    print()
    print(f"[{name}]")
    print(f"N                  : {len(samples)}")

    print(
        f"orig 평균 반복률   : "
        f"{mean(orig_rates) * 100:.4f}%"
    )

    print(
        f"rep 평균 반복률    : "
        f"{mean(rep_rates) * 100:.4f}%"
    )

    print(
        f"변화량             : "
        f"{mean(changes) * 100:+.4f}%p"
    )

    print(
        f"반복 감소          : "
        f"{reduced} "
        f"({reduced / len(samples) * 100:.2f}%)"
    )

    print(
        f"반복 증가          : "
        f"{increased} "
        f"({increased / len(samples) * 100:.2f}%)"
    )

    print(
        f"변화 없음          : "
        f"{unchanged} "
        f"({unchanged / len(samples) * 100:.2f}%)"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--orig",
        default="results/opt_predictions_orig.jsonl"
    )

    parser.add_argument(
        "--rep",
        default="results/opt_predictions_rep.jsonl"
    )

    parser.add_argument(
        "--ngram",
        type=int,
        default=3
    )

    args = parser.parse_args()

    orig = load_jsonl(args.orig)
    rep = load_jsonl(args.rep)

    common_ids = sorted(
        set(orig.keys()) & set(rep.keys())
    )

    print("=" * 80)
    print("ORIG → REP REPETITION ANALYSIS")
    print("=" * 80)

    print(f"orig samples : {len(orig)}")
    print(f"rep samples  : {len(rep)}")
    print(f"common       : {len(common_ids)}")
    print(f"n-gram       : {args.ngram}")

    transitions = {
        "CC": [],
        "CW": [],
        "WC": [],
        "WW": [],
    }

    all_samples = []

    for sample_id in common_ids:
        o = orig[sample_id]
        r = rep[sample_id]

        o_stats = repetition_stats(
            o.get("prediction_raw"),
            n=args.ngram
        )

        r_stats = repetition_stats(
            r.get("prediction_raw"),
            n=args.ngram
        )

        item = {
            "id": sample_id,
            "orig_rate": o_stats["rate"],
            "rep_rate": r_stats["rate"],
            "orig_repeated": o_stats["repeated"],
            "rep_repeated": r_stats["repeated"],
        }

        all_samples.append(item)

        transition = classify_transition(o, r)

        transitions[transition].append(item)

    # 전체
    print_group(
        "전체",
        all_samples
    )

    # CC / CW / WC / WW
    print()
    print("=" * 80)
    print("정답 변화별 repetition 변화")
    print("=" * 80)

    print_group(
        "CC",
        transitions["CC"]
    )

    print_group(
        "CW",
        transitions["CW"]
    )

    print_group(
        "WC",
        transitions["WC"]
    )

    print_group(
        "WW",
        transitions["WW"]
    )

    # 요약표
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        f"{'구분':<8}"
        f"{'N':>6}"
        f"{'orig':>12}"
        f"{'rep':>12}"
        f"{'변화':>12}"
    )

    print("-" * 55)

    for name in ["CC", "CW", "WC", "WW"]:
        items = transitions[name]

        if not items:
            continue

        orig_rate = mean(
            x["orig_rate"] for x in items
        )

        rep_rate = mean(
            x["rep_rate"] for x in items
        )

        change = rep_rate - orig_rate

        print(
            f"{name:<8}"
            f"{len(items):>6}"
            f"{orig_rate * 100:>11.4f}%"
            f"{rep_rate * 100:>11.4f}%"
            f"{change * 100:>+11.4f}%p"
        )


if __name__ == "__main__":
    main()