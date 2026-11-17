| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| c1b_rft_describe | prompt=describe_cot, ckpt=c1b_rft_merged | 900 | 63.2% | 64.3% | +1.1 | 89 / 79 | 0.488 | n/a | 3299 | 40 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
