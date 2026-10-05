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

# Instruction appended after the question/options.
#   official : MMMU llava1.5.yaml wording (the baseline). Do not change it.
#   cot_open : official for multiple-choice; step-by-step + "Answer:" line
#              for open questions only (they are answered in ~5 tokens with
#              the official wording).
#   cot_all  : step-by-step + "Answer:" line for both question types.
MC_DIRECT = "Answer with the option's letter from the given choices directly."
OPEN_DIRECT = "Answer the question using a single word or phrase."
DESCRIBE_COT = ("First describe precisely what the image shows (for example every note, "
                "symbol, atom, bond, label or value that matters), then reason step by "
                "step, and write the final answer on the last line in the form "
                "'Answer: {fmt}'.")
MC_COT = ("Think step by step, then write the final answer on the last line "
          "in the form 'Answer: <letter>'.")
OPEN_COT = ("Solve the problem step by step, then write the final answer on "
            "the last line in the form 'Answer: <value>'.")
DESCRIPT_MC = DESCRIBE_COT.format(fmt="<letter>")
DESCRIPT_OPEN = DESCRIBE_COT.format(fmt="<value>")
PROMPT_VARIANTS = {
    "official": {"mc": MC_DIRECT, "open": OPEN_DIRECT},
    # perception probe: transcribe the image first, then reason
    "describe_cot": {"mc": DESCRIPT_MC, "open": DESCRIPT_OPEN},
    "cot_open": {"mc": MC_DIRECT, "open": OPEN_COT},
    "cot_all": {"mc": MC_COT, "open": OPEN_COT},
}
PROMPT_VARIANT = "official"  # set by run_mmmu.py --prompt_variant
# Text-only ablation: replace every image with the literal text "[image]"
# so we can measure how much the answer depends on the picture.
NO_IMAGES = False  # set by run_mmmu.py --no_images


def _instruction(kind: str) -> str:
    return PROMPT_VARIANTS[PROMPT_VARIANT][kind]


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

        if NO_IMAGES:
            content.append({"type": "text", "text": "[image]"})
        else:
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
            f"{_instruction('mc')}"
        )

    return (
        f"{question}\n\n"
        f"{_instruction('open')}"
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
                "text": _instruction("mc"),
            }
        )
    else:
        content.append(
            {
                "type": "text",
                "text": "\n\n" + _instruction("open"),
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

    out: Dict[str, Any] = {"prompt": prompt}
    if mm_data:  # text-only ablation sends no multimodal payload at all
        out["multi_modal_data"] = mm_data
        out["mm_processor_kwargs"] = video_kwargs
    return out
