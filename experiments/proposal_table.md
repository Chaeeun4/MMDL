| run | settings | n | baseline | run | Δ (%p) | W→C / C→W | McNemar p | seed-noise flips | mean tokens | length stops |
|---|---|---|---|---|---|---|---|---|---|---|
| p1_noise_seed1234 | seed=1234 | 900 | 61.1% | 60.1% | -1.0 | 25 / 34 | 0.298 | — (this is the noise run) | 2871 | 54 |
| abl_cot_open | prompt=cot_open, question_types=open | 53 | 17.0% | 39.6% | +22.6 | 15 / 3 | 0.00754 | 1 (net -1) | 4884 | 4 |
| abl_temp0 | T=0.0 | 900 | 61.1% | 58.6% | -2.6 | 21 / 44 | 0.00592 | 59 (net -9) | 3819 | 94 |
| lora_smoke_eval | ckpt=lora_smoke_merged, subjects=Art,Accounting | 60 | 68.3% | 46.7% | -21.7 | 4 / 17 | 0.0072 | 4 (net +0) | 2 | 0 |
| p3_sym_cot | prompt=cot_all, img_types=Sheet Music,Chemical Structures,Sketches and Drafts,Technical Blueprints | 95 | 32.6% | 40.0% | +7.4 | 16 / 9 | 0.23 | 5 (net -1) | 9654 | 23 |
| p4_sym_textonly | text-only, img_types=Sheet Music,Chemical Structures,Sketches and Drafts,Technical Blueprints | 95 | 32.6% | 24.2% | -8.4 | 7 / 15 | 0.134 | 5 (net -1) | 822 | 2 |
| p5_sym_hires | min_px=1048576, img_types=Sheet Music,Chemical Structures,Sketches and Drafts,Technical Blueprints | 95 | 32.6% | 37.9% | +5.3 | 11 / 6 | 0.332 | 5 (net -1) | 2225 | 5 |
| p6_sym_describe | prompt=describe_cot, img_types=Sheet Music,Chemical Structures,Sketches and Drafts,Technical Blueprints | 95 | 32.6% | 45.3% | +12.6 | 22 / 10 | 0.0501 | 5 (net -1) | 10226 | 25 |

How to read: Δ and flips are computed on the questions each run covered. 'seed-noise flips' = how many of those questions changed correctness between the baseline and a rerun with only a different seed; a real effect needs W→C minus C→W well above that net noise and a small McNemar p.
