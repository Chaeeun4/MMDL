| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| primus_only |  | 900 | 61.1% | 63.2% | +2.1 | 108 / 89 | 0.2 | n/a | 3828 | 77 |
| pubchem_only |  | 900 | 61.1% | 61.7% | +0.6 | 111 / 106 | 0.786 | n/a | 3039 | 65 |
| both |  | 900 | 61.1% | 60.8% | -0.3 | 101 / 104 | 0.889 | n/a | 2696 | 54 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
