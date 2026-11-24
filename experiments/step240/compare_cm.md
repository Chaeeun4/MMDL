| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| cm_final_official | ckpt=cm_ft_merged | 900 | 61.1% | 61.1% | +0.0 | 51 / 51 | 1 | n/a | 1990 | 21 |
| cm_step240_full | ckpt=cm_ft_step240_merged | 900 | 61.1% | 62.6% | +1.4 | 59 / 46 | 0.241 | n/a | 1584 | 4 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
