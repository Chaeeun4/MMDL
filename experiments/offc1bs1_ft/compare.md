| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| offc1bs1_final_full | ckpt=offc1bs1_ft_merged | 900 | 61.1% | 63.2% | +2.1 | 100 / 81 | 0.181 | n/a | 3265 | 37 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
