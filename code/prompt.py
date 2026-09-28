"""
MMMU prompt/message construction for Qwen3-VL.

Sources:
- Official MMMU prompt configuration:
  https://github.com/MMMU-Benchmark/MMMU/blob/main/mmmu/configs/llava1.5.yaml
- Official MMMU data/prompt utilities:
  https://github.com/MMMU-Benchmark/MMMU
- Qwen3-VL multimodal input format:
  https://github.com/QwenLM/Qwen3-VL
"""

from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Tuple


IMAGE_REF_RE = re.compile(r"<image\s+(\d+)>")


# Qwen3-VL visual token budget.
# qwen-vl-utils for Qwen3-VL uses a 32-pixel resize factor.
# These are only *defaults*; run_mmmu.py exposes them as --min_pixels /
# --max_pixels so the resolution budget is documented/reproducible instead
# of buried in a hardcoded constant.
MIN_PIXELS = 1280 * 32 * 32
MAX_PIXELS = 5120 * 32 * 32


def parse_options(options: str | List[str]) -> List[str]:
    """Parse MMMU's Python-literal options field."""
    if isinstance(options, list):
        return [str(x) for x in options]

    parsed = ast.literal_eval(options)
    if not isinstance(parsed, list):
        raise ValueError(f"MMMU options must be a list, got: {type(parsed)}")

    return [str(x) for x in parsed]


def _image_by_index(sample: Dict[str, Any], image_index: int) -> Any:
    """Get image_N from the original MMMU sample."""
    key = f"image_{image_index}"

    images = sample.get("images", {})
    if key not in images:
        raise KeyError(f"Image reference <image {image_index}> not found.")
    return images[key]


def _append_text_with_images(
    content: List[Dict[str, Any]],
    text: str,
    sample: Dict[str, Any],
    min_pixels: int = MIN_PIXELS,
    max_pixels: int = MAX_PIXELS,
) -> None:
    """Convert <image N> references into Qwen multimodal content items."""
    cursor = 0

    for match in IMAGE_REF_RE.finditer(text):
        if match.start() > cursor:
            content.append(
                {"type": "text", "text": text[cursor : match.start()]}
            )

        image_index = int(match.group(1))
        image = _image_by_index(sample, image_index)

        if image is None:
            raise ValueError(
                f"{sample['id']}: referenced image_{image_index} is missing."
            )

        content.append(
            {
                "type": "image",
                "image": image,
                "min_pixels": min_pixels,
                "max_pixels": max_pixels,
            }
        )
        cursor = match.end()

    if cursor < len(text):
        content.append({"type": "text", "text": text[cursor:]})
    elif cursor == 0:
        content.append({"type": "text", "text": text})


def build_prompt_text(sample: Dict[str, Any]) -> str:
    """Build the text template used by the official MMMU evaluation config.

    For multiple-choice:
        question
        blank line
        (A) option
        (B) option
        ...
        Answer with the option's letter from the given choices directly.

    For open questions:
        question
        blank line
        Answer the question using a single word or phrase.
    """
    question = sample["question"]
    options = parse_options(sample["options"])

    if options:
        choices = "\n".join(
            f"({chr(ord('A') + i)}) {option}"
            for i, option in enumerate(options)
        )
        return (
            f"{question}\n\n"
            f"{choices}\n"
            f"Answer with the option's letter from the given choices directly."
        )

    return (
        f"{question}\n\n"
        f"Answer the question using a single word or phrase."
    )


def build_messages(
    sample: Dict[str, Any],
    min_pixels: int = MIN_PIXELS,
    max_pixels: int = MAX_PIXELS,
) -> List[Dict[str, Any]]:
    """Build a Qwen3-VL user message while preserving image references."""
    question = sample["question"]
    options = parse_options(sample["options"])

    content: List[Dict[str, Any]] = []

    # Keep the exact textual order of <image N> references in the question.
    _append_text_with_images(content, question, sample, min_pixels, max_pixels)

    if options:
        content.append({"type": "text", "text": "\n\n"})
        for i, option in enumerate(options):
            content.append(
                {
                    "type": "text",
                    "text": f"({chr(ord('A') + i)}) ",
                }
            )
            _append_text_with_images(
                content, option, sample, min_pixels, max_pixels
            )
            content.append({"type": "text", "text": "\n"})

        content.append(
            {
                "type": "text",
                "text": (
                    "Answer with the option's letter from the given choices "
                    "directly."
                ),
            }
        )
    else:
        content.append(
            {
                "type": "text",
                "text": (
                    "\n\nAnswer the question using a single word or phrase."
                ),
            }
        )

    return [{"role": "user", "content": content}]


def build_vllm_input(
    sample: Dict[str, Any],
    processor: Any,
    min_pixels: int = MIN_PIXELS,
    max_pixels: int = MAX_PIXELS,
) -> Dict[str, Any]:
    """Convert a sample to the vLLM multimodal input format."""
    messages = build_messages(sample, min_pixels, max_pixels)

    prompt = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )

    # Import here so importing this module does not require qwen-vl-utils.
    from qwen_vl_utils import process_vision_info

    image_inputs, video_inputs, video_kwargs = process_vision_info(
        messages,
        image_patch_size=processor.image_processor.patch_size,
        return_video_kwargs=True,
        return_video_metadata=True,
    )

    mm_data: Dict[str, Any] = {}
    if image_inputs is not None:
        mm_data["image"] = image_inputs
    if video_inputs is not None:
        mm_data["video"] = video_inputs

    return {
        "prompt": prompt,
        "multi_modal_data": mm_data,
        "mm_processor_kwargs": video_kwargs,
    }
