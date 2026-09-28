import json
import argparse
import statistics
from transformers import AutoTokenizer


def load_jsonl(path):
    data = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))

    return data


def get_token_count(tokenizer, text):
    if text is None:
        return None

    text = str(text)

    tokens = tokenizer.encode(
        text,
        add_special_tokens=False
    )

    return len(tokens)


def percentile(values, p):
    if not values:
        return None

    values = sorted(values)

    k = (len(values) - 1) * p
    f = int(k)
    c = f + 1

    if c >= len(values):
        return values[-1]

    return values[f] + (values[c] - values[f]) * (k - f)


def print_stats(name, values):
    values = [v for v in values if v is not None]

    if not values:
        print(f"{name}: 데이터 없음")
        return

    print(f"\n{name}")
    print("-" * 60)

    print(f"N        : {len(values)}")
    print(f"평균     : {statistics.mean(values):.1f}")
    print(f"중앙값   : {statistics.median(values):.1f}")
    print(f"최소     : {min(values)}")
    print(f"최대     : {max(values)}")
    print(f"P90      : {percentile(values, 0.90):.1f}")
    print(f"P95      : {percentile(values, 0.95):.1f}")
    print(f"P99      : {percentile(values, 0.99):.1f}")

    for limit in [2048, 3072, 4096, 8192]:
        count = sum(v >= limit for v in values)
        print(
            f">= {limit:4d} : "
            f"{count:4d} "
            f"({count / len(values) * 100:.2f}%)"
        )


def analyze_file(name, path, tokenizer):
    data = load_jsonl(path)

    print()
    print("=" * 80)
    print(name)
    print(path)
    print("=" * 80)

    # 전체
    all_tokens = []

    # 정답
    correct_tokens = []

    # 오답
    wrong_tokens = []

    for item in data:
        raw = item.get("prediction_raw")

        if raw is None:
            continue

        n_tokens = get_token_count(tokenizer, raw)

        if n_tokens is None:
            continue

        all_tokens.append(n_tokens)

        if item.get("correct") is True:
            correct_tokens.append(n_tokens)

        elif item.get("correct") is False:
            wrong_tokens.append(n_tokens)

    print_stats("전체", all_tokens)
    print_stats("정답", correct_tokens)
    print_stats("오답", wrong_tokens)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default="Qwen/Qwen3-VL-4B-Instruct"
    )

    parser.add_argument(
        "--orig",
        default="results/opt_predictions_orig.jsonl"
    )

    parser.add_argument(
        "--tmp",
        default="results/opt_predictions_tmp.jsonl"
    )

    parser.add_argument(
        "--rep",
        default="results/opt_predictions_rep.jsonl"
    )

    args = parser.parse_args()

    print("Tokenizer loading...")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True
    )

    files = [
        ("ORIG", args.orig),
        ("TMP", args.tmp),
        ("REP", args.rep),
    ]

    for name, path in files:
        analyze_file(name, path, tokenizer)


if __name__ == "__main__":
    main()