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

    correct = s
