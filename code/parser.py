"""
Deterministic MMMU answer parser.

The multiple-choice extraction logic is adapted from the official MMMU
evaluation utility:
https://github.com/MMMU-Benchmark/MMMU/blob/main/eval/eval_utils.py

Important:
- This is for the original MMMU benchmark, NOT MMMU-Pro.
- The original MMMU code randomly selects a choice when parsing fails.
  This implementation deliberately returns None instead. That makes the
  baseline deterministic and prevents a parser failure from becoming a
  random correct answer.
- No GPT/model judge is used.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


PUNCTUATION = [",", ".", "!", "?", ";", ":", "'"]


def get_multi_choice_info(
    options: List[str],
) -> Tuple[Dict[str, str], List[str]]:
    """Create A/B/C/... labels from the option list."""
    index2ans: Dict[str, str] = {}
    all_choices: List[str] = []

    for i, option in enumerate(options):
        letter = chr(ord("A") + i)
        index2ans[letter] = option
        all_choices.append(letter)

    return index2ans, all_choices


def parse_multi_choice_response(
    response: str,
    all_choices: List[str],
    index2ans: Dict[str, str],
) -> Optional[str]:
    """Parse a multiple-choice response using MMMU's rule ordering.

    Rule order:
    1. If the response contains the last `Answer:` marker, inspect the text
       after it and look for a unique option label.
    2. Look for parenthesized labels such as (A).
    3. Look for standalone labels such as `A `.
    4. Look for labels followed by a period such as `A.`.
    5. If no label is found and the response is long enough, look for the
       literal option text.
    6. If several candidates exist, use the last occurrence, matching the
       original MMMU strategy.
    7. If nothing can be parsed, return None instead of choosing randomly.
    """
    if not isinstance(response, str):
        return None

    response = response.strip()
    if not response:
        return None

    # MMMU's official parser first checks the final "Answer:" section.
    last_answer_pos = response.rfind("Answer:")
    if last_answer_pos != -1:
        answer_str = response[last_answer_pos + len("Answer:") :].strip()
        matching_options = [
            option for option in all_choices if option in answer_str
        ]
        if len(matching_options) == 1:
            return matching_options[0]

    for char in PUNCTUATION:
        response = response.strip(char)
    response = f" {response} "

    index_ans = True
    ans_with_brack = False
    candidates: List[str] = []

    # (A), (B), ...
    for choice in all_choices:
        if f"({choice})" in response:
            candidates.append(choice)
            ans_with_brack = True

    # A, B, ... as standalone tokens (space on both sides, matching the
    # official MMMU eval_utils.py rule -- a trailing-space-only check would
    # false-match words that happen to end in a choice letter, e.g. "USA ").
    if not candidates:
        for choice in all_choices:
            if f" {choice} " in response:
                candidates.append(choice)

    # A., B., ...
    if not candidates:
        for choice in all_choices:
            if f"{choice}." in response:
                candidates.append(choice)

    # Option-text fallback from the official MMMU parser.
    if not candidates and len(response.split()) > 5:
        lower_response = response.lower()
        for index, answer_text in index2ans.items():
            if answer_text.lower() in lower_response:
                candidates.append(index)
        index_ans = False

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # Several candidates: select the last-mentioned candidate.
    start_indexes: List[int] = []

    if index_ans:
        if ans_with_brack:
            for candidate in candidates:
                start_indexes.append(response.rfind(f"({candidate})"))
        else:
            for candidate in candidates:
                start_indexes.append(response.rfind(f" {candidate} "))
    else:
        lower_response = response.lower()
        for candidate in candidates:
            start_indexes.append(
                lower_response.rfind(index2ans[candidate].lower())
            )

    return candidates[start_indexes.index(max(start_indexes))]


def normalize_string(value: Any) -> List[Any]:
    """Normalize a short-answer string/number following MMMU conventions.

    Returns a list (matching the official MMMU `normalize_str`), because a
    single-character string normalizes to *two* padded variants
    (" x ", "x ") instead of one. The padding exists to stop trivial
    substring matches during open-answer scoring: without it, a gold
    answer of "A" would match any prediction that merely contains the
    letter "a" somewhere (e.g. inside "data" or "above").
    """
    if not isinstance(value, str):
        return [value]

    value = value.strip()
    if not value:
        return [value]

    try:
        number = float(value.replace(",", ""))
        return [round(number, 2)]
    except ValueError:
        value = value.lower()
        if len(value) == 1:
            return [f" {value}", f"{value} "]
        return [value]


def extract_numbers(text: str) -> List[str]:
    """Extract numeric strings using the official MMMU regex family."""
    pattern_commas = r"-?\b\d{1,3}(?:,\d{3})+\b"
    pattern_scientific = r"-?\d+(?:\.\d+)?[eE][+-]?\d+"
    pattern_simple = (
        r"-?(?:\d+\.\d+|\.\d+|\d+\b)"
        r"(?![eE][+-]?\d+)(?![,\d])"
    )

    return (
        re.findall(pattern_commas, text)
        + re.findall(pattern_scientific, text)
        + re.findall(pattern_simple, text)
    )


def parse_open_response(response: str) -> List[Any]:
    """Parse MMMU short-answer/open response deterministically."""
    if not isinstance(response, str):
        return []

    response = response.strip().strip(".").lower()

    sub_responses = re.split(r"\.\s(?=[A-Z])|\n", response)
    indicators = [
        "could be ",
        "so ",
        "is ",
        "thus ",
        "therefore ",
        "final ",
        "answer ",
        "result ",
    ]

    key_responses: List[str] = []

    for index, resp in enumerate(sub_responses):
        current_indicators = list(indicators)
        if index == len(sub_responses) - 1:
            current_indicators.append("=")

        shortest: Optional[str] = None
        for indicator in current_indicators:
            if indicator in resp:
                candidate = resp.split(indicator)[-1].strip()
                if shortest is None or len(candidate) < len(shortest):
                    shortest = candidate

        if shortest and shortest not in [":", ",", ".", "!", "?", ";", "'"]:
            key_responses.append(shortest)

    if not key_responses:
        key_responses = [response]

    pred_list: List[Any] = list(key_responses)

    for item in key_responses:
        pred_list.extend(extract_numbers(item))

    normalized: List[Any] = []
    for item in pred_list:
        normalized.extend(normalize_string(item))

    # Preserve order while removing duplicates.
    unique: List[Any] = []
    for item in normalized:
        if item not in unique:
            unique.append(item)

    return unique


def parse_answer(
    response: str,
    question_type: str,
    options: List[str],
) -> Any:
    """Parse a model response according to MMMU question type."""
    if question_type == "multiple-choice":
        index2ans, all_choices = get_multi_choice_info(options)
        return parse_multi_choice_response(
            response, all_choices, index2ans
        )

    return parse_open_response(response)
