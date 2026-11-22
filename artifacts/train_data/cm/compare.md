| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| cm_final_full | prompt=describe_cot, ckpt=cm_ft_merged | 900 | 63.2% | 63.7% | +0.4 | 94 / 90 | 0.825 | n/a | 3458 | 49 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
