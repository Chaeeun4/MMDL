"""
MMMU test dataset loader.

Sources:
- MMMU dataset: https://huggingface.co/datasets/MMMU/MMMU
- Assignment specification: direct loading of each MMMU subject config
  from the Hugging Face dataset with the pinned revision.

This file intentionally does NOT download/convert MMMU_DEV_VAL.tsv.
The assignment uses the official Hugging Face MMMU dataset directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from datasets import load_dataset


DATASET_NAME = "MMMU/MMMU"
DATASET_REVISION = "98e6ac0cb9b7b2cd2c991b85a50762edc4aedc68"
SPLIT = "test"
TEST_SIZE = 10_500
IMAGE_COLUMNS = tuple(f"image_{i}" for i in range(1, 8))

SUBJECTS: List[str] = [
    "Accounting",
    "Agriculture",
    "Architecture_and_Engineering",
    "Art",
    "Art_Theory",
    "Basic_Medical_Science",
    "Biology",
    "Chemistry",
    "Clinical_Medicine",
    "Computer_Science",
    "Design",
    "Diagnostics_and_Laboratory_Medicine",
    "Economics",
    "Electronics",
    "Energy_and_Power",
    "Finance",
    "Geography",
    "History",
    "Literature",
    "Manage",
    "Marketing",
    "Materials",
    "Math",
    "Mechanical_Engineering",
    "Music",
    "Pharmacy",
    "Physics",
    "Psychology",
    "Public_Health",
    "Sociology",
]


def with_images(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Decode only the images for the prompt being built."""
    dataset, index = sample["_image_row"]
    return {**sample, "images": {
        key: image for key, image in dataset[index].items() if image is not None
    }}


def load_mmmu_test(
    answer_path: Path,
    data_root: str | None = None,
    subjects: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """Load pinned MMMU test questions and join the public labels by ID."""
    with answer_path.open(encoding="utf-8") as file:
        answers = json.load(file)

    selected_subjects = subjects or SUBJECTS

    unknown = [s for s in selected_subjects if s not in SUBJECTS]
    if unknown:
        raise ValueError(f"Unknown MMMU subjects: {unknown}")

    samples: List[Dict[str, Any]] = []

    for subject in selected_subjects:
        dataset = load_dataset(
            DATASET_NAME,
            subject,
            split=SPLIT,
            revision=DATASET_REVISION,
            cache_dir=data_root,
        )

        image_columns = [name for name in IMAGE_COLUMNS if name in dataset.column_names]
        image_rows = dataset.select_columns(image_columns)
        text_rows = dataset.remove_columns(image_columns)
        for index, row in enumerate(text_rows):
            question_id = row["id"]
            label = answers.get(question_id)
            gold = label.get("ground_truth") if label else None
            if (not label or label.get("question_type") != row["question_type"]
                    or gold is None or gold == [] or (isinstance(gold, str) and not gold.strip())):
                raise ValueError(f"{question_id}: missing or incompatible public test label")
            samples.append(
                {
                    "id": row["id"],
                    "subject": subject,
                    "question": row["question"],
                    "options": row["options"],
                    "answer": gold,
                    "question_type": row["question_type"],
                    "subfield": row.get("subfield", ""),
                    "img_type": row.get("img_type", ""),
                    "topic_difficulty": row.get("topic_difficulty", ""),
                    # Gold rationale shipped with MMMU; kept for later
                    # error analysis (never shown to the model).
                    "explanation": row.get("explanation", ""),
                    "_image_row": (image_rows, index),
                }
            )

    if not subjects and len(samples) != TEST_SIZE:
        raise RuntimeError(f"Loaded {len(samples)} test samples, expected {TEST_SIZE}.")
    if len({sample["id"] for sample in samples}) != len(samples):
        raise RuntimeError("Duplicate MMMU test question IDs.")

    return samples
