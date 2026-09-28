import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_jsonl(path):
    data = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            item = json.loads(line)
            data[item["id"]] = item

    return data


def is_correct(item):
    return item.get("correct", False) is True


def short_text(text, n=500):
    if text is None:
        return "(None)"

    text = str(text).replace("\n", " ")
    text = " ".join(text.split())

    if len(text) <= n:
        return text

    return "..." + text[-n:]


def get_finish_reason(item):
    return item.get("finish_reason", "N/A")


def get_completion_tokens(item):
    value = item.get("completion_tokens")

    if value is None:
        return None

    try:
        return int(value)
    except Exception:
        return None


def accuracy(data):
    if not data:
        return 0.0

    correct = sum(is_correct(x) for x in data.values())
    return correct / len(data) * 100


def none_count(data):
    return sum(
        1 for x in data.values()
        if x.get("prediction") is None
    )


def print_basic_stats(name, data):
    total = len(data)
    correct = sum(is_correct(x) for x in data.values())
    none = none_count(data)

    finish = Counter(get_finish_reason(x) for x in data.values())

    tokens = [
        get_completion_tokens(x)
        for x in data.values()
        if get_completion_tokens(x) is not None
    ]

    print()
    print("=" * 80)
    print(f"{name}")
    print("=" * 80)

    print(f"Total              : {total}")
    print(f"Correct            : {correct}")
    print(f"Accuracy           : {correct / total * 100:.2f}%")
    print(f"Prediction=None    : {none} ({none / total * 100:.2f}%)")

    print()
    print("Finish reason:")
    for k, v in finish.items():
        print(f"  {k:<15}: {v} ({v / total * 100:.2f}%)")

    if tokens:
        print()
        print("Completion tokens:")
        print(f"  avg              : {sum(tokens) / len(tokens):.1f}")
        print(f"  min              : {min(tokens)}")
        print(f"  max              : {max(tokens)}")
        print(f"  >= 4000          : {sum(t >= 4000 for t in tokens)}")


def print_transition(name1, data1, name2, data2):
    ids = sorted(set(data1) & set(data2))

    counter = Counter()

    for id_ in ids:
        a = is_correct(data1[id_])
        b = is_correct(data2[id_])

        if a and b:
            key = "correct -> correct"
        elif a and not b:
            key = "correct -> wrong"
        elif not a and b:
            key = "wrong -> correct"
        else:
            key = "wrong -> wrong"

        counter[key] += 1

    print()
    print("=" * 80)
    print(f"{name1} -> {name2}")
    print("=" * 80)

    for key in [
        "correct -> correct",
        "correct -> wrong",
        "wrong -> correct",
        "wrong -> wrong",
    ]:
        value = counter[key]
        print(f"{key:<22}: {value:4d} ({value / len(ids) * 100:.2f}%)")

    print()
    print(
        f"Accuracy change: "
        f"{accuracy(data2) - accuracy(data1):+.2f}%p"
    )


def print_answer_changes(name1, data1, name2, data2):
    ids = sorted(set(data1) & set(data2))

    changed = []

    for id_ in ids:
        p1 = data1[id_].get("prediction")
        p2 = data2[id_].get("prediction")

        if p1 != p2:
            changed.append(id_)

    print()
    print("=" * 80)
    print(f"Prediction changes: {name1} -> {name2}")
    print("=" * 80)

    print(f"Changed: {len(changed)} / {len(ids)}")
    print(f"Rate   : {len(changed) / len(ids) * 100:.2f}%")

    return changed


def print_changed_cases(
    name1,
    data1,
    name2,
    data2,
    only="all",
    max_cases=30,
):
    ids = sorted(set(data1) & set(data2))

    selected = []

    for id_ in ids:
        a = data1[id_]
        b = data2[id_]

        a_correct = is_correct(a)
        b_correct = is_correct(b)

        if only == "wrong_to_correct":
            if not a_correct and b_correct:
                selected.append(id_)

        elif only == "correct_to_wrong":
            if a_correct and not b_correct:
                selected.append(id_)

        elif only == "prediction_changed":
            if a.get("prediction") != b.get("prediction"):
                selected.append(id_)

        else:
            selected.append(id_)

    print()
    print("=" * 80)
    print(
        f"{name1} -> {name2} "
        f"[{only}] "
        f"showing {min(len(selected), max_cases)} / {len(selected)}"
    )
    print("=" * 80)

    for i, id_ in enumerate(selected[:max_cases], 1):
        a = data1[id_]
        b = data2[id_]

        print()
        print("-" * 80)
        print(f"[{i}] {id_}")
        print("-" * 80)

        print(f"Subject : {a.get('subject')}")
        print(f"Gold    : {a.get('gold')}")

        print(
            f"{name1:<8}: "
            f"{a.get('prediction')} "
            f"({'CORRECT' if is_correct(a) else 'WRONG'})"
        )

        print(
            f"{name2:<8}: "
            f"{b.get('prediction')} "
            f"({'CORRECT' if is_correct(b) else 'WRONG'})"
        )

        print()
        print(f"[{name1} metadata]")
        print(f"finish_reason     : {get_finish_reason(a)}")
        print(f"completion_tokens : {get_completion_tokens(a)}")

        print()
        print(f"[{name2} metadata]")
        print(f"finish_reason     : {get_finish_reason(b)}")
        print(f"completion_tokens : {get_completion_tokens(b)}")

        print()
        print(f"[{name1} last 500 chars]")
        print(short_text(a.get("prediction_raw"), 500))

        print()
        print(f"[{name2} last 500 chars]")
        print(short_text(b.get("prediction_raw"), 500))


def print_subject_comparison(datasets):
    subjects = sorted(
        set().union(
            *[
                {x.get("subject") for x in data.values()}
                for data in datasets.values()
            ]
        )
    )

    print()
    print("=" * 100)
    print("SUBJECT COMPARISON")
    print("=" * 100)

    header = (
        f"{'Subject':<40}"
        f"{'orig':>10}"
        f"{'tmp':>10}"
        f"{'rep':>10}"
    )

    print(header)
    print("-" * 100)

    for subject in subjects:
        values = []

        for name in ["orig", "tmp", "rep"]:
            data = datasets[name]

            subset = [
                x for x in data.values()
                if x.get("subject") == subject
            ]

            if subset:
                acc = sum(is_correct(x) for x in subset) / len(subset) * 100
                values.append(f"{acc:>8.2f}%")
            else:
                values.append(f"{'N/A':>9}")

        print(
            f"{subject:<40}"
            f"{values[0]}"
            f"{values[1]}"
            f"{values[2]}"
        )


def print_answer_transition_matrix(name1, data1, name2, data2):
    """
    prediction 자체가 어떻게 변했는지 확인.
    예:
        A -> A
        A -> B
        B -> C
        None -> B
    """

    counter = Counter()

    ids = sorted(set(data1) & set(data2))

    for id_ in ids:
        p1 = data1[id_].get("prediction")
        p2 = data2[id_].get("prediction")

        p1 = "None" if p1 is None else str(p1)
        p2 = "None" if p2 is None else str(p2)

        counter[(p1, p2)] += 1

    print()
    print("=" * 80)
    print(f"ANSWER TRANSITIONS: {name1} -> {name2}")
    print("=" * 80)

    for (a, b), count in sorted(
        counter.items(),
        key=lambda x: -x[1]
    ):
        if a != b:
            print(f"{a:>5} -> {b:<5}: {count}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--orig", required=True)
    parser.add_argument("--tmp", required=True)
    parser.add_argument("--rep", required=True)

    parser.add_argument(
        "--max_cases",
        type=int,
        default=30,
        help="각 변화 유형에서 출력할 최대 문제 수",
    )

    args = parser.parse_args()

    orig = load_jsonl(args.orig)
    tmp = load_jsonl(args.tmp)
    rep = load_jsonl(args.rep)

    datasets = {
        "orig": orig,
        "tmp": tmp,
        "rep": rep,
    }

    print("\n")
    print("#" * 80)
    print("MMMU PREDICTION ANALYSIS")
    print("#" * 80)

    # ---------------------------------------------------------
    # 1. 기본 통계
    # ---------------------------------------------------------

    for name, data in datasets.items():
        print_basic_stats(name, data)

    # ---------------------------------------------------------
    # 2. 정확도 transition
    # ---------------------------------------------------------

    print_transition("orig", orig, "tmp", tmp)
    print_transition("orig", orig, "rep", rep)
    print_transition("tmp", tmp, "rep", rep)

    # ---------------------------------------------------------
    # 3. 실제 prediction 변경량
    # ---------------------------------------------------------

    print_answer_changes("orig", orig, "tmp", tmp)
    print_answer_changes("orig", orig, "rep", rep)
    print_answer_changes("tmp", tmp, "rep", rep)

    # ---------------------------------------------------------
    # 4. 답변 자체가 어떻게 바뀌었는지
    # ---------------------------------------------------------

    print_answer_transition_matrix("orig", orig, "tmp", tmp)
    print_answer_transition_matrix("orig", orig, "rep", rep)

    # ---------------------------------------------------------
    # 5. 과목별
    # ---------------------------------------------------------

    print_subject_comparison(datasets)

    # ---------------------------------------------------------
    # 6. 중요한 사례 출력
    # ---------------------------------------------------------

    # Temperature
    print_changed_cases(
        "orig",
        orig,
        "tmp",
        tmp,
        only="wrong_to_correct",
        max_cases=args.max_cases,
    )

    print_changed_cases(
        "orig",
        orig,
        "tmp",
        tmp,
        only="correct_to_wrong",
        max_cases=args.max_cases,
    )

    # Repetition penalty
    print_changed_cases(
        "orig",
        orig,
        "rep",
        rep,
        only="wrong_to_correct",
        max_cases=args.max_cases,
    )

    print_changed_cases(
        "orig",
        orig,
        "rep",
        rep,
        only="correct_to_wrong",
        max_cases=args.max_cases,
    )

    print("\n")
    print("#" * 80)
    print("ANALYSIS FINISHED")
    print("#" * 80)


if __name__ == "__main__":
    main()
