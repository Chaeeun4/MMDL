| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| c1b_final_official | ckpt=c1b_rft_merged | 900 | 61.1% | 62.4% | +1.3 | 46 / 34 | 0.219 | n/a | 2100 | 27 |
| offc1b_final_full | ckpt=offc1b_ft_merged | 900 | 61.1% | 66.1% | +5.0 | 119 / 74 | 0.00147 | n/a | 3439 | 44 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
