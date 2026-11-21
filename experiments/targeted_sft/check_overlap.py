"""Find training/evaluation overlap without unpacking the training images."""

import argparse
import ast
from collections import Counter, defaultdict, OrderedDict
import csv
from hashlib import sha256
from itertools import islice
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
from tempfile import TemporaryDirectory
import unicodedata
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageOps
import pyarrow.parquet as pq


MMMU_REV = "98e6ac0cb9b7b2cd2c991b85a50762edc4aedc68"
PRO_REV = "0d7426df4ccb3d8704a992fe6850abee7c262127"
DCT = np.cos(np.pi / 32 * np.arange(8)[:, None] * (np.arange(32) + 0.5))


def normalized(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"<image(?:\s*\d+)?>", " ", text)
    return " ".join(re.findall(r"[^\W_]+", text))


def options_text(text):
    if isinstance(text, str):
        if text.lstrip().startswith("["):
            try:
                return options_text(ast.literal_eval(text))
            except (ValueError, SyntaxError):
                pass
        return re.sub(r"(?m)^\s*[A-Z][.)]\s+", "", text)
    return " ".join(map(str, text or []))


def shingles(text):
    words = text.split()
    return {" ".join(words[i:i + 8]) for i in range(len(words) - 7)}


def fingerprint(blob):
    with Image.open(io.BytesIO(blob)) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        pixels = sha256(f"{image.width}x{image.height}:".encode() + image.tobytes()).hexdigest()
        gray = np.asarray(image.convert("L").resize((32, 32), Image.Resampling.LANCZOS))
    # Omit the DC coefficient, which primarily captures average brightness.
    coefficients = (DCT @ gray @ DCT.T).ravel()[1:]
    bits = np.packbits(coefficients > np.median(coefficients))
    return sha256(blob).hexdigest(), pixels, int.from_bytes(bits.tobytes(), "big")


class Index:
    def __init__(self, distance, text_fraction):
        self.distance = distance
        self.text_fraction = text_fraction
        self.band_count = distance + 1
        self.band_width = (64 + distance) // self.band_count
        self.text = defaultdict(set)
        self.ngram = defaultdict(set)
        self.exact = defaultdict(set)
        self.bands = defaultdict(set)
        self.hash_refs = defaultdict(set)

    def bands_for(self, phash):
        mask = (1 << self.band_width) - 1
        return ((i, (phash >> (i * self.band_width)) & mask) for i in range(self.band_count))

    def add_text(self, key, question, options):
        q = normalized(question)
        combined = normalized(question + " " + options_text(options))
        for value in {q, combined} - {""}:
            self.text[value].add(key)
        for gram in shingles(combined):
            self.ngram[gram].add(key)

    def add_image(self, key, fp):
        raw, pixels, phash = fp
        self.exact[raw].add(key)
        self.exact[pixels].add(key)
        if phash not in self.hash_refs:
            for band in self.bands_for(phash):
                self.bands[band].add(phash)
        self.hash_refs[phash].add(key)

    def text_hits(self, question, options):
        q = normalized(question)
        combined = normalized(question + " " + options_text(options))
        for key in self.text.get(q, set()) | self.text.get(combined, set()):
            yield key, "text_exact", 1
        grams = shingles(combined)
        counts = Counter(key for gram in grams for key in self.ngram.get(gram, ()))
        for key, n in counts.items():
            if n / len(grams) >= self.text_fraction:
                yield key, "text_8gram_fraction", round(n / len(grams), 4)

    def image_hits(self, fp):
        raw, pixels, phash = fp
        for key in self.exact.get(raw, set()) | self.exact.get(pixels, set()):
            yield key, "image_exact", 0
        nearby = set().union(*(self.bands.get(band, ()) for band in self.bands_for(phash)))
        for other in nearby:
            distance = (phash ^ other).bit_count()
            if distance <= self.distance:
                for key in self.hash_refs[other]:
                    yield key, "image_phash_distance", distance


def benchmark_files(args):
    mmmu = args.hub_cache / "datasets--MMMU--MMMU" / "snapshots" / MMMU_REV
    pro = args.hub_cache / "datasets--MMMU--MMMU_Pro" / "snapshots" / args.pro_revision
    sets = {}
    for split, count in (("dev", 150), ("validation", 900), ("test", 10500)):
        files = sorted(mmmu.glob(f"*/{split}-*.parquet"))
        if len({p.parent for p in files}) != 30:
            raise ValueError(f"MMMU {split}: require all 30 subjects in {mmmu}")
        sets[f"MMMU/{split}"] = files, count
    for config in ("standard (4 options)", "standard (10 options)", "vision"):
        sets[f"MMMU-Pro/{config}"] = sorted((pro / config).glob("test-*.parquet")), 1730
    for scope, (files, count) in sets.items():
        actual = sum(pq.ParquetFile(f).metadata.num_rows for f in files)
        if actual != count:
            raise ValueError(f"{scope}: expected {count} rows, found {actual}")
    return sets


def ocr(blob):
    result = subprocess.run(
        ["tesseract", "stdin", "stdout", "-l", "eng"],
        input=blob, capture_output=True, timeout=90, check=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def build_index(args, sets, semantic=None):
    index = Index(args.phash_distance, args.ngram_fraction)
    counts = {}
    for scope, (files, expected) in sets.items():
        count = Counter()
        for file_number, file in enumerate(files, 1):
            if file_number == 1 or file_number % 10 == 0:
                print(f"{scope}: file {file_number}/{len(files)}", flush=True)
            parquet = pq.ParquetFile(file)
            fields = parquet.schema_arrow.names
            image_cols = [name for name in fields if re.fullmatch(r"image(?:_\d+)?", name)]
            cols = [name for name in ("id", "question", "options", *image_cols) if name in fields]
            if "id" not in cols or not image_cols:
                raise ValueError(f"{file}: missing id or image columns")
            for batch in parquet.iter_batches(batch_size=4, columns=cols):
                for row in batch.to_pylist():
                    key = f"{scope}/{row['id']}"
                    question = row.get("question") or ""
                    for col in image_cols:
                        if (cell := row[col]) is None:
                            continue
                        blob = cell.get("bytes") if isinstance(cell, dict) else cell
                        if not isinstance(blob, bytes):
                            raise ValueError(f"{key}/{col}: image bytes missing")
                        image_key = f"{key}/{col}"
                        fp = fingerprint(blob)
                        index.add_image(image_key, fp)
                        if semantic is not None:
                            semantic.add(image_key, fp[1], blob)
                        count["images"] += 1
                        if scope == "MMMU-Pro/vision" and args.vision_ocr:
                            try:
                                recognized = ocr(blob).strip()
                            except (subprocess.SubprocessError, OSError) as error:
                                raise RuntimeError(f"{image_key}: OCR failed") from error
                            if not recognized:
                                raise ValueError(f"{image_key}: OCR returned empty text")
                            question += " " + recognized
                            count["ocr_images"] += 1
                    if question.strip():
                        index.add_text(key, question, row.get("options"))
                        count["text_rows"] += 1
                    count["rows"] += 1
        if count["rows"] != expected:
            raise ValueError(f"{scope}: read {count['rows']} rows, expected {expected}")
        if scope == "MMMU-Pro/vision" and args.vision_ocr:
            if count["ocr_images"] != expected:
                raise ValueError(f"{scope}: OCR covered {count['ocr_images']} images, expected {expected}")
        counts[scope] = dict(count)
        print(scope, dict(count), flush=True)
    return index, counts


class CandidateImages:
    def __init__(self, root, sources, stack):
        raw = root / "raw"
        self.archives = {}
        if "ai2d" in sources:
            self.archives["ai2d"] = stack.enter_context(ZipFile(raw / "ai2d/ai2d-all.zip"))
        if "ecd" in sources:
            self.archives["ecd"] = stack.enter_context(tarfile.open(raw / "ecd/images.tar"))
            self.ecd = {
                Path(m.name).stem: m for m in self.archives["ecd"]
                if m.isfile() and Path(m.name).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            }
        if "virl" in sources:
            self.archives["virl"] = stack.enter_context(ZipFile(raw / "virl/images.zip"))
            self.virl_parquet = pq.ParquetFile(raw / "virl/39Krelease.parquet")
            self.virl = None

    def raw_rows(self, root):
        archive = self.archives["ai2d"]
        for member in sorted(archive.namelist()):
            if not member.startswith("ai2d/questions/") or not member.endswith(".json"):
                continue
            item = json.loads(archive.read(member))
            image_id = item["imageName"]
            for question, row in item["questions"].items():
                yield {
                    "source": "ai2d", "sample_id": row["questionId"],
                    "group_id": f"ai2d/{image_id}", "question": question,
                    "choices": row["answerTexts"],
                }

        path = root / "raw/ecd/ECD_QAs_All.json"
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        # Keep the original array index as sample_id and group questions by image.
        for i in sorted(range(len(data)), key=lambda i: str(data[i]["image_id"])):
            row = data[i]
            yield {
                "source": "ecd", "sample_id": str(i),
                "group_id": "ecd/" + str(row["image_id"]).zfill(6), "question": row["question"],
            }
        del data

        for batch in self.virl_parquet.iter_batches(batch_size=1024, columns=["qid", "question", "image"]):
            for row in batch.to_pylist():
                yield {
                    "source": "virl", "sample_id": row["qid"],
                    "group_id": f"virl/{row['qid']}", "question": row["question"], "image_members": row["image"],
                }

    def names(self, row):
        source = row["source"]
        if source == "virl":
            if "image_members" in row:
                return row["image_members"] or []
            if self.virl is None:
                self.virl = {
                    item["qid"]: item["image"] for item in
                    self.virl_parquet.read(columns=["qid", "image"]).to_pylist()
                }
            return self.virl[row["sample_id"]] or []
        prefix, sep, image_id = row["group_id"].partition("/")
        if not sep or prefix != source or "/" in image_id or not image_id:
            raise ValueError(f"Invalid image group: {row['group_id']}")
        if source == "ai2d":
            return [f"ai2d/images/{image_id}"]
        return [self.ecd[image_id].name]

    def read(self, source, name):
        archive = self.archives[source]
        if source == "ecd":
            with archive.extractfile(self.ecd[Path(name).stem]) as file:
                return file.read()
        return archive.read(name)


def scan_candidates(rows, images, index, semantic, batch_size, out):
    candidate_counts = Counter()
    source_counts = Counter()
    seen = set()
    image_count = match_count = 0

    # Retain matching records, not image bytes, for repeated images across batches.
    image_cache = OrderedDict()

    with (out / "candidates.csv").open("w", encoding="utf-8-sig", newline="") as candidate_file, \
         (out / "matches.csv").open("w", encoding="utf-8-sig", newline="") as match_file:
        candidates = csv.writer(candidate_file)
        matches = csv.writer(match_file)
        candidates.writerow(("source", "sample_id", "group_id", "images_checked", "status"))
        matches.writerow(("source", "sample_id", "archive_member", "benchmark_id", "method", "score"))
        size = max(256, batch_size)
        iterator = iter(rows)
        while batch := list(islice(iterator, size)):
            memberships = []
            for row in batch:
                source, sample_id = row["source"], row["sample_id"]
                identity = source, sample_id
                if identity in seen:
                    raise ValueError(f"Duplicate candidate: {source}/{sample_id}")
                seen.add(identity)
                if not (row.get("question") or "").strip():
                    raise ValueError(f"{source}/{sample_id}: blank question")
                names = images.names(row)
                if not names:
                    raise ValueError(f"{source}/{sample_id}: no image to check")
                memberships.append(tuple((source, name) for name in names))

            # Process each image at most once in this batch, including shared chart images.
            batch_hits = {}
            pending = []
            for key in dict.fromkeys(key for keys in memberships for key in keys):
                if key in image_cache:
                    image_cache.move_to_end(key)
                    batch_hits[key] = image_cache[key]
                else:
                    blob = images.read(*key)
                    batch_hits[key] = list(index.image_hits(fingerprint(blob)))
                    if semantic is not None:
                        pending.append((key, blob))
                        if len(pending) == batch_size:
                            add_semantic_results(semantic, pending, batch_hits)
            if pending:
                add_semantic_results(semantic, pending, batch_hits)
            for key, hits in batch_hits.items():
                image_cache[key] = hits
                if len(image_cache) > 4096:
                    image_cache.popitem(last=False)

            for row, keys in zip(batch, memberships):
                source, sample_id = row["source"], row["sample_id"]
                hits = {(key, kind, score, "") for key, kind, score in
                        index.text_hits(row["question"], row.get("choices") or "")}
                for key in keys:
                    hits.update((ref, kind, score, key[1]) for ref, kind, score in batch_hits[key])
                status = "review_needed" if hits else "no_match_found"
                candidates.writerow((source, sample_id, row["group_id"], len(keys), status))
                matches.writerows((source, sample_id, image, key, kind, score)
                                  for key, kind, score, image in sorted(hits))
                candidate_counts[status] += 1
                source_counts[source] += 1
                image_count += len(keys)
                match_count += len(hits)
            total = len(seen)
            if total // 10000 != (total - len(batch)) // 10000:
                print(f"Training candidates checked: {total}", flush=True)
    if not seen:
        raise ValueError("No candidates to inspect")
    return candidate_counts, source_counts, image_count, match_count


def add_semantic_results(semantic, pending, batch_hits):
    for (key, _), hits in zip(pending, semantic.find([blob for _, blob in pending])):
        batch_hits[key].extend(hits)
    pending.clear()


def main():
    from contextlib import ExitStack

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.home() / "datasets/targeted_sft")
    parser.add_argument("--hub-cache", type=Path, default=Path.home() / ".cache/huggingface/hub")
    parser.add_argument("--pro-revision", default=PRO_REV)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--manifest", type=Path, nargs="+")
    inputs.add_argument("--all-raw", action="store_true", help="Scan every AI2D, ECD and ViRL question")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phash-distance", type=int, default=6)
    parser.add_argument("--ngram-fraction", type=float, default=0.5)
    parser.add_argument("--vision-ocr", action="store_true", help="Run local Tesseract on Pro Vision")
    parser.add_argument("--full", action="store_true", help="Require both Vision OCR and SigLIP")
    parser.add_argument("--siglip-model", help="Locally cached Hugging Face model ID or model directory")
    parser.add_argument("--siglip-revision", help="Pinned cache revision for the model")
    parser.add_argument("--siglip-device", default="auto", help="auto, cpu, cuda or cuda:N")
    parser.add_argument("--siglip-batch-size", type=int, default=16)
    parser.add_argument("--siglip-threshold", type=float, default=0.92)
    args = parser.parse_args()
    args.full = args.full or args.all_raw
    if args.full and not args.siglip_model:
        parser.error("--full requires --siglip-model")
    args.vision_ocr = args.vision_ocr or args.full
    if args.siglip_batch_size <= 0 or not 0 < args.siglip_threshold <= 1:
        parser.error("invalid SigLIP batch size or threshold")
    if not 0 <= args.phash_distance <= 12 or not 0 < args.ngram_fraction <= 1:
        parser.error("invalid pHash distance or n-gram fraction")
    for path in args.manifest or []:
        if not path.is_file():
            parser.error(f"candidate CSV does not exist: {path}. Pass an existing --manifest file.")
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    if args.vision_ocr and not shutil.which("tesseract"):
        parser.error("--vision-ocr requires tesseract on PATH")

    if args.vision_ocr:
        languages = subprocess.check_output(["tesseract", "--list-langs"], text=True)
        if "eng" not in languages.splitlines():
            parser.error("Tesseract English language data (eng) is required")

    rows = []
    for path in args.manifest or []:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not {"source", "sample_id", "group_id", "question"} <= set(reader.fieldnames or ()):
                raise ValueError(f"{path}: missing required manifest columns")
            for row in reader:
                if any(not (row.get(k) or "").strip()
                       for k in ("source", "sample_id", "group_id", "question")):
                    raise ValueError(f"{path}:{reader.line_num}: blank required manifest field")
                rows.append(row)
    supported = {"ai2d", "ecd", "virl"}
    sources = supported if args.all_raw else {r["source"] for r in rows}
    if not sources or sources - supported:
        raise ValueError(f"Empty manifest or unsupported sources: {sources}")

    sets = benchmark_files(args)
    semantic = None
    if args.siglip_model:
        from siglip_search import SiglipSearch
        semantic = SiglipSearch(args.siglip_model, args.siglip_revision, args.siglip_device,
                                args.siglip_batch_size, args.siglip_threshold)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        images = CandidateImages(args.root, sources, stack)
        index, coverage = build_index(args, sets, semantic)
        if semantic is not None:
            semantic.finish()

        temporary = stack.enter_context(TemporaryDirectory(dir=args.out.parent, prefix=".overlap-"))
        output = Path(temporary) / "results"
        output.mkdir()
        candidates = images.raw_rows(args.root) if args.all_raw else rows
        counts, source_counts, image_count, match_count = scan_candidates(
            candidates, images, index, semantic, args.siglip_batch_size, output
        )
        summary = {
            "benchmark_coverage": coverage,
            "mmmu_revision": MMMU_REV, "mmmu_pro_revision": args.pro_revision,
            "methods": ["normalized_text", "8gram", "file_and_decoded_pixel_sha256", "phash"],
            "vision_ocr": args.vision_ocr,
            "siglip": semantic is not None,
            "full_mode": args.full,
            "candidate_scope": "all_raw" if args.all_raw else "manifest",
            "candidate_rows": sum(source_counts.values()),
            "candidate_images": image_count,
            "candidate_source_counts": dict(source_counts),
            "phash_max_distance": args.phash_distance, "ngram_min_fraction": args.ngram_fraction,
            "manifests": [str(p.resolve()) for p in args.manifest or []],
            "candidate_counts": dict(counts),
            "match_rows": match_count,
        }
        if args.vision_ocr:
            summary["methods"].append("vision_ocr")
            summary["ocr_config"] = {
                "engine": subprocess.check_output(["tesseract", "--version"], text=True).splitlines()[0],
                "language": "eng",
            }
        if semantic is not None:
            summary["methods"].append("siglip_cosine")
            summary["siglip_config"] = {
                "model": semantic.model_path, "revision": semantic.revision,
                "device": str(semantic.device), "cosine_threshold": semantic.threshold,
                "unique_benchmark_images": len(semantic.keys),
            }
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        if args.out.exists():
            raise FileExistsError(args.out)
        output.rename(args.out)
        print(json.dumps(summary["candidate_counts"]), flush=True)


if __name__ == "__main__":
    main()
