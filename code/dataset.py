"""
MMMU validation dataset loader.

Sources:
- MMMU dataset: https://huggingface.co/datasets/MMMU/MMMU
- Assignment specification: direct loading of each MMMU subject config
  from the Hugging Face dataset with the pinned revision.

This file intentionally does NOT download/convert MMMU_DEV_VAL.tsv.
The assignment uses the official Hugging Face MMMU dataset directly.
"""


import io
from pathlib import Path
from typing import Any, Dict, List

from datasets import load_dataset


DATASET_NAME = "MMMU/MMMU"
DATASET_REVISION = "98e6ac0cb9b7b2cd2c991b85a50762edc4aedc68"
SPLIT = "validation"
PRO_DATASET_NAME = "MMMU/MMMU_Pro"
PRO_REVISION = "0d7426df4ccb3d8704a992fe6850abee7c262127"
PRO_SETTINGS = {"standard10": "standard (10 options)", "vision": "vision"}

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
            path=DATASET_NAME,
            name=subject,
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
                    # Gold rationale shipped with MMMU; kept for later
                    # error analysis (never shown to the model).
                    "explanation": row.get("explanation", ""),
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


def load_mmmu_pro(hub_cache: str, setting: str, subjects=None, limit=None):
    """Read the pinned Pro test parquet files directly from the existing Hub cache."""
    from PIL import Image
    import pyarrow.parquet as pq

    snapshot = Path(hub_cache) / "datasets--MMMU--MMMU_Pro" / "snapshots" / PRO_REVISION
    files = sorted((snapshot / PRO_SETTINGS[setting]).glob("test-*.parquet"))
    expected_files = 4 if setting == "vision" else 2
    if len(files) != expected_files or not all(path.is_file() for path in files):
        raise ValueError(f"Missing {setting} parquet shards under {snapshot}")
    shards = [pq.ParquetFile(path) for path in files]
    if sum(shard.metadata.num_rows for shard in shards) != 1730:
        raise ValueError(f"{setting}: expected 1730 MMMU-Pro test rows")

    samples = []
    for shard in shards:
        for batch in shard.iter_batches(batch_size=8):
            for row in batch.to_pylist():
                if subjects and row["subject"] not in subjects:
                    continue
                images = {}
                for key, cell in row.items():
                    if (key == "image" or key.startswith("image_")) and cell is not None:
                        if not isinstance(cell, dict) or not cell.get("bytes"):
                            raise ValueError(f"{row['id']}: missing image bytes in {key}")
                        images["image_1" if key == "image" else key] = Image.open(
                            io.BytesIO(cell["bytes"])
                        )
                if not images:
                    raise ValueError(f"{row['id']}: no images")
                samples.append({
                    "id": row["id"], "subject": row["subject"],
                    "question": row.get("question", ""),
                    "options": row["options"], "answer": row["answer"],
                    "question_type": "multiple-choice", "images": images,
                    "img_type": row.get("img_type", ""),
                    "topic_difficulty": row.get("topic_difficulty", ""),
                    "pro_setting": setting,
                })
                if limit is not None and len(samples) == limit:
                    return samples
    if not samples:
        raise ValueError(f"{setting}: no test rows match requested subjects")
    return samples
