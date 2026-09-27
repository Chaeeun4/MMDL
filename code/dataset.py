"""
MMMU validation dataset loader.

Sources:
- MMMU dataset: https://huggingface.co/datasets/MMMU/MMMU
- Assignment specification: direct loading of each MMMU subject config
  from the Hugging Face dataset with the pinned revision.

This file intentionally does NOT download/convert MMMU_DEV_VAL.tsv.
The assignment uses the official Hugging Face MMMU dataset directly.
"""

from __future__ import annotations

from typing import Any, Dict, List

from datasets import load_dataset


DATASET_NAME = "MMMU/MMMU"
DATASET_REVISION = "98e6ac0cb9b7b2cd2c991b85a50762edc4aedc68"
SPLIT = "validation"

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


def _normalize_image(image: Any) -> Any:
    """Return the dataset image object unchanged.

    Hugging Face's Image feature is decoded to a PIL image when accessed.
    Keeping the object as-is lets qwen-vl-utils/vLLM handle the vision input.
    """
    return image


def load_mmmu_validation(
    data_root: str | None = None,
    subjects: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """Load all requested MMMU validation samples.

    Args:
        data_root:
            Local Hugging Face cache directory. This is a cache location,
            not a TSV dataset directory.
        subjects:
            Optional subject subset for debugging. The normal assignment run
            must use all 30 subjects.

    Returns:
        A flat list of samples. Each sample contains the gold answer so that
        run_mmmu.py can pass it to evaluator.py after inference.
    """
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

        if len(dataset) != 30:
            raise ValueError(
                f"{subject}: expected 30 validation examples, got {len(dataset)}"
            )

        for row in dataset:
            samples.append(
                {
                    "id": row["id"],
                    "subject": subject,
                    "question": row["question"],
                    "options": row["options"],
                    "answer": row["answer"],
                    "question_type": row["question_type"],
                    "subfield": row.get("subfield", ""),
                    "img_type": row.get("img_type", ""),
                    "topic_difficulty": row.get("topic_difficulty", ""),
                    "images": {
                        f"image_{i}": _normalize_image(row[f"image_{i}"])
                        for i in range(1, 8)
                        if row.get(f"image_{i}") is not None
                    },
                }
            )

    expected = len(selected_subjects) * 30
    if len(samples) != expected:
        raise RuntimeError(
            f"Loaded {len(samples)} samples, expected {expected}."
        )

    return samples
