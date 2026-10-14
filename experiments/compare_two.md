| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| abl_cot_open | prompt=cot_open, question_types=open | 53 | 17.0% | 39.6% | +22.6 | 15 / 3 | 0.00754 | n/a | 4884 | 4 |
| p3_sym_cot | prompt=cot_all, img_types=Sheet Music,Chemical Structures,Sketches and Drafts,Technical Blueprints | 95 | 32.6% | 40.0% | +7.4 | 16 / 9 | 0.23 | n/a | 9654 | 23 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
