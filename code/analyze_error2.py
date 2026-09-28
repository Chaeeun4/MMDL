import json
import re
from collections import Counter, defaultdict

from parser import parse_answer, get_multi_choice_info


FILE_PATH = "results/opt_predictions.jsonl"


# ---------------------------------------------------------
# parser.py와 동일한 로직을 사용하되,
# "어떤 규칙으로 답을 찾았는지"를 별도로 기록한다.
# ---------------------------------------------------------
def detect_parse_method(response, options):
    if not isinstance(response, str):
        return None, "invalid_response"

    response = response.strip()

    if not response:
        return None, "empty"

    index2ans, all_choices = get_multi_choice_info(options)

    # 1. Answer: 뒤
    last_answer_pos = response.rfind("Answer:")
    if last_answer_pos != -1:
        answer_str = response[
            last_answer_pos + len("Answer:"):
        ].strip()

        matching = [
            choice
            for choice in all_choices
            if choice in answer_str
        ]

        if len(matching) == 1:
            return matching[0], "Answer:"

    # parser.py와 동일하게 전처리
    punctuation = [",", ".", "!", "?", ";", ":", "'"]

    for char in punctuation:
        response = response.strip(char)

    response = f" {response} "

    candidates = []
    ans_with_brack = False
    index_ans = True

    # 2. (A)
    for choice in all_choices:
        if f"({choice})" in response:
            candidates.append(choice)
            ans_with_brack = True

    if candidates:
        method = "bracket"

    else:
        # 3. standalone A
        for choice in all_choices:
            if f" {choice} " in response:
                candidates.append(choice)

        if candidates:
            method = "standalone"

        else:
            # 4. A.
            for choice in all_choices:
                if f"{choice}." in response:
                    candidates.append(choice)

            if candidates:
                method = "period"

            else:
                # 5. option text
                if len(response.split()) > 5:
                    lower_response = response.lower()

                    for choice, answer_text in index2ans.items():
                        if answer_text.lower() in lower_response:
                            candidates.append(choice)

                    index_ans = False

                    if candidates:
                        method = "option_text"
                    else:
                        method = "parse_failed"

                else:
                    method = "parse_failed"

    if not candidates:
        return None, method

    # 하나면 그대로
    if len(candidates) == 1:
        return candidates[0], method

    # 여러 후보 → parser.py와 동일하게 마지막 등장 선택
    positions = []

    if index_ans:
        if ans_with_brack:
            for candidate in candidates:
                positions.append(
                    response.rfind(f"({candidate})")
                )
        else:
            for candidate in candidates:
                positions.append(
                    response.rfind(f" {candidate} ")
                )
    else:
        lower_response = response.lower()

        for candidate in candidates:
            positions.append(
                lower_response.rfind(
                    index2ans[candidate].lower()
                )
            )

    selected = candidates[positions.index(max(positions))]

    return selected, method + "_multiple"


# ---------------------------------------------------------
# main
# ---------------------------------------------------------

total = 0
correct = 0

parse_method_counter = Counter()
wrong_method_counter = Counter()

subject_total = defaultdict(int)
subject_correct = defaultdict(int)

parse_failures = []
disagreements = []
wrong_samples = []

with open(FILE_PATH, "r", encoding="utf-8") as f:

    for line in f:
        data = json.loads(line)

        total += 1

        raw = data.get("prediction_raw", "")
        gold = data.get("gold")
        saved_prediction = data.get("prediction")

        options = data.get("options", [])

        # -------------------------------------------------
        # raw response를 다시 parser에 넣음
        # -------------------------------------------------

        reparsed_prediction, parse_method = detect_parse_method(
            raw,
            options,
        )

        parse_method_counter[parse_method] += 1

        # -------------------------------------------------
        # 기존 prediction과 재파싱 결과가 다른 경우
        # -------------------------------------------------

        if reparsed_prediction != saved_prediction:

            disagreements.append({
                "id": data.get("id"),
                "gold": gold,
                "saved_prediction": saved_prediction,
                "reparsed_prediction": reparsed_prediction,
                "parse_method": parse_method,
                "raw": raw[:1000],
            })

        # -------------------------------------------------
        # 최종 평가
        # -------------------------------------------------

        is_correct = reparsed_prediction == gold

        if is_correct:
            correct += 1

        subject = data.get("subject", "Unknown")

        subject_total[subject] += 1

        if is_correct:
            subject_correct[subject] += 1

        if reparsed_prediction is None:

            parse_failures.append({
                "id": data.get("id"),
                "subject": subject,
                "gold": gold,
                "raw": raw[:1000],
            })

        if not is_correct:
            wrong_method_counter[parse_method] += 1

            if len(wrong_samples) < 10:
                wrong_samples.append({
                    "id": data.get("id"),
                    "subject": subject,
                    "gold": gold,
                    "prediction": reparsed_prediction,
                    "method": parse_method,
                    "raw": raw[:500],
                })


# ---------------------------------------------------------
# 결과 출력
# ---------------------------------------------------------

print("=" * 70)
print("MMMU Parser / Evaluation Analysis")
print("=" * 70)

print(f"\n전체 문항       : {total}")
print(f"재파싱 정답     : {correct}")
print(f"재파싱 오답     : {total - correct}")
print(f"정확도          : {correct / total * 100:.2f}%")

print("\n" + "-" * 70)
print("1. Parser 사용 규칙 분포")
print("-" * 70)

for method, count in parse_method_counter.most_common():
    ratio = count / total * 100
    print(f"{method:25s}: {count:4d} ({ratio:5.2f}%)")


print("\n" + "-" * 70)
print("2. Parser 실패")
print("-" * 70)

print(f"parse 실패(None): {len(parse_failures)}개")

for item in parse_failures[:10]:
    print(
        f"\n[{item['id']}] "
        f"subject={item['subject']} "
        f"gold={item['gold']}"
    )
    print(item["raw"])


print("\n" + "-" * 70)
print("3. 기존 prediction과 재파싱 결과 불일치")
print("-" * 70)

print(f"불일치: {len(disagreements)}개")

for item in disagreements[:10]:
    print(f"\n[{item['id']}]")
    print(f"Gold              : {item['gold']}")
    print(f"기존 prediction   : {item['saved_prediction']}")
    print(f"재파싱 prediction : {item['reparsed_prediction']}")
    print(f"Parser method     : {item['parse_method']}")
    print(f"Raw               : {item['raw']}")


print("\n" + "-" * 70)
print("4. 오답의 Parser 규칙 분포")
print("-" * 70)

for method, count in wrong_method_counter.most_common():
    print(f"{method:25s}: {count:4d}")


print("\n" + "-" * 70)
print("5. 과목별 정확도")
print("-" * 70)

for subject in sorted(subject_total):
    total_sub = subject_total[subject]
    correct_sub = subject_correct[subject]

    print(
        f"{subject:35s}: "
        f"{correct_sub / total_sub * 100:5.2f}% "
        f"({correct_sub}/{total_sub})"
    )


print("\n" + "-" * 70)
print("6. 대표 오답")
print("-" * 70)

for i, item in enumerate(wrong_samples, 1):

    print(f"\n[{i}] {item['id']} ({item['subject']})")
    print(f"Gold       : {item['gold']}")
    print(f"Prediction : {item['prediction']}")
    print(f"Parser     : {item['method']}")
    print(f"Raw        : {item['raw']}")

print("\n" + "=" * 70)