# C1: diverse-prompt rejection-sampling fine-tuning (RFT)

Reproduce: `setsid nohup bash scripts/run_c1_rft.sh > /data/$USER/rft/c1/queue.log 2>&1 < /dev/null &`

## Setup
- Training pool: ViRL39K (public, verifiable answers). 14 questions overlapping MMMU test/MMMU-Pro were removed (`virl39k_contamination.json`, `code/check_contamination.py`). No MMMU data is used for training.
- Generation: the base Qwen3-VL-4B-Instruct (no external model) answered 6,000 questions with 4 independent prompt strategies (describe / cot / check / concise). That gave 24,000 samples in 3.3 h.
  - pass@1 was 0.658 and pass@any was **0.818**, so using diverse strategies covered more questions.
- Selection (`code/gen_rft.py select`): a sample was kept only if it was correct, stopped normally, used ≤1500 tokens, ended with `Answer:` and had no loop words. At most 2 samples per question, **shortest first**, 30% of all-correct questions kept. The result was 4,667 SFT samples and 1,846 DPO pairs (not used yet).
- Training: LoRA r16 / α32 on the language layers, lr 1e-4 cosine, batch 16, 1 epoch = 291 steps. It took 1.0 h, peaked at 14.3 GB and had no OOM. One fixed describe_cot instruction was used for every sample.
- Eval: MMMU-val 900, official Instruct sampling recipe, `--prompt_variant describe_cot`, same pipeline as the baseline.

## Results (MMMU-val 900)

| | base, official prompt | base, describe_cot | **C1, describe_cot** |
|---|---|---|---|
| overall | 61.1 | 63.2 | **63.6** |
| open (53) | 17.0 | 43.4 | 34.0 |
| multiple choice (847) | 63.9 | 64.5 | 65.4 |
| symbolic images (86, first img_type) | 30.2 | 41.9 | 43.0 |
| bottom-6 subjects (180) | 38.9 | 44.4 | 49.4 |
| top-15 subjects (450) | 73.3 | 74.0 | 74.7 |
| mean / median tokens | 2384 / 8 | 5433 / 709 | **2226 / 210** |
| length stops | 40 | 109 | **23** |
| summed decode time | 21.1 h | 60.7 h | **16.1 h** |

- C1 vs the base model with the same prompt: +0.3 %p, 101 W→C / 98 C→W, McNemar p = 0.89. **Not an improvement** by our rule (`compare.md`).
- C1 vs the official baseline: +2.4 %p, p = 0.107. Also not significant (`compare_vs_official.md`).
- Length clearly improved. Of the 109 questions where the base model hit the length cap, C1 answered 51 correctly.

## Diagnosis → C1b
Shortest-first selection made the training answers very short (about 285 tokens). The model learned to finish quickly, but open-question accuracy fell from 43.4% to 34.0%. Also, 1,281 hard questions had no clean sample and were never trained on.

C1b: pick samples by random or median length within the ≤1500 cap, add more open questions, and resample the hard questions.
