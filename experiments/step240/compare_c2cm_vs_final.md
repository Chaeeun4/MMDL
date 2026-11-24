| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| c2cm_step240_full | ckpt=c2cm_ft_step240_merged | 900 | 59.7% | 60.8% | +1.1 | 42 / 32 | 0.295 | n/a | 1439 | 9 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
