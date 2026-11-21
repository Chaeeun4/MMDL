"""Select image-backed pilot questions and export LLaMA-Factory ShareGPT JSON."""

import argparse
import csv
import json
from pathlib import Path
import random
import re
import tarfile
from zipfile import ZipFile


RELATION = re.compile(
    r"\b(?:connect\w*|arrow\w*|flow\w*|direction|pathway|leads to|feeds on)\b", re.I
)
CALCULATION = re.compile(
    r"\b(?:difference|how much (?:more|less)|ratio|percent(?:age)?|sum|"
    r"total|average|convert|conversion|increase[ds]? by|decrease[ds]? by)\b", re.I
)


def ai2d_candidates(archive):
    for member in sorted(archive.namelist()):
        if not member.startswith("ai2d/questions/") or not member.endswith(".json"):
            continue
        item = json.loads(archive.read(member))
        image = item["imageName"]
        for question, row in item["questions"].items():
            choices = row["answerTexts"]
            index = row["correctAnswer"]
            if not RELATION.search(question) or not 0 <= index < len(choices):
                continue
            if any(re.search(r"<image>|\.(png|jpg|jpeg)$", c, re.I) for c in choices):
                continue
            yield row["questionId"], image, question, tuple(choices), choices[index]


def ecd_candidates(root):
    data = json.loads((root / "ECD_QAs_All.json").read_text(encoding="utf-8"))
    for i, row in enumerate(data):
        if row.get("split") != "reasoning" or not CALCULATION.search(row["question"]):
            continue
        if not row["answer"].strip():
            continue
        image_id = str(row["image_id"])
        if image_id.isdigit():
            yield str(i), image_id.zfill(6), row["question"], (), row["answer"]


def write_pilot(root, source, candidates, read_image, count, seed):
    random.Random(seed).shuffle(candidates)
    selected = []
    used = set()
    for row in candidates:
        if row[1] in used:
            continue
        selected.append(row)
        used.add(row[1])
        if len(selected) == count:
            break
    if len(selected) != count:
        raise ValueError(f"{source}: found {len(selected)} distinct images, need {count}")

    # Read every selected image before writing files, so absent inputs fail early.
    image_data = {row[1]: read_image(row[1]) for row in selected}
    prepared = root / "prepared"
    output = prepared / f"{source}_pilot_sharegpt.json"
    review = prepared / f"{source}_pilot_review.csv"
    images_dir = prepared / "images" / source
    records = []
    manifest = []
    images_dir.mkdir(parents=True, exist_ok=True)
    for sample_id, image_id, question, choices, answer in selected:
        suffix, blob = image_data[image_id]
        filename = f"{Path(image_id).stem}{suffix}"
        (images_dir / filename).write_bytes(blob)
        image_path = f"targeted_sft/prepared/images/{source}/{filename}"
        options = "\n".join(f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices))
        prompt = f"<image>\n{question}" + (f"\n{options}" if options else "")
        records.append({
            "conversations": [{"from": "human", "value": prompt},
                              {"from": "gpt", "value": answer}],
            "images": [image_path],
        })
        manifest.append({
            "source": source,
            "sample_id": sample_id,
            "group_id": f"{source}/{image_id}",
            "image": image_path,
            "question": question,
            "choices": options,
            "answer": answer,
            "split_status": "unverified" if source == "ai2d" else "source_train",
            "review_status": "pending",
            "overlap_status": "not_checked",
        })
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with review.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    print(f"{len(records)} samples: {output}, {review}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("ai2d", "ecd"))
    parser.add_argument("--root", type=Path, default=Path.home() / "datasets/targeted_sft")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--seed", type=int, default=3407)
    args = parser.parse_args()
    if args.count <= 0:
        parser.error("--count must be positive")
    raw = args.root / "raw" / args.source
    if args.source == "ai2d":
        with ZipFile(raw / "ai2d-all.zip") as archive:
            write_pilot(args.root, args.source, list(ai2d_candidates(archive)),
                        lambda name: (Path(name).suffix, archive.read(f"ai2d/images/{name}")),
                        args.count, args.seed)
    else:
        with tarfile.open(raw / "images.tar") as archive:
            members = {Path(m.name).stem: m for m in archive if m.isfile()
                       and Path(m.name).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}}
            candidates = [row for row in ecd_candidates(raw) if row[1] in members]

            def read_image(name):
                member = members[name]
                with archive.extractfile(member) as file:
                    return Path(member.name).suffix, file.read()

            write_pilot(args.root, args.source, candidates, read_image, args.count, args.seed)


if __name__ == "__main__":
    main()
