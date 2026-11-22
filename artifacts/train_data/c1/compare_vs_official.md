| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| p1_noise_seed1234 | seed=1234 | 900 | 61.1% | 60.1% | -1.0 | 25 / 34 | 0.298 | — (this is the noise run) | 2871 | 54 |
| base_describe | prompt=describe_cot | 900 | 61.1% | 63.2% | +2.1 | 107 / 88 | 0.197 | 59 (net -9) | 5433 | 109 |
| c1_rft_describe | prompt=describe_cot, ckpt=c1_rft_merged | 900 | 61.1% | 63.6% | +2.4 | 96 / 74 | 0.107 | 59 (net -9) | 2226 | 23 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
