| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| abl_cot_open | prompt=cot_open, question_types=open | 53 | 17.0% | 39.6% | +22.6 | 15 / 3 | 0.00754 | n/a | 4884 | 4 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
