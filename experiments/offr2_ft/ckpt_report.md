# Checkpoint report: offr2

Held-out loss (lower is better; `replay` rising = forgetting of the general data).

| step | self |
|---|---|
| 0 | 0.347 |
| 200 | 0.139 |
| 400 | 0.134 |
| 403 | 0.134 |

MMMU-val accuracy on the same questions, base model vs checkpoint (30 questions per subject, sampled decoding: a difference of 2-3 questions is within noise).

| checkpoint | subject | n | base | ckpt | W→C | C→W |
|---|---|---|---|---|---|---|
| offr2_final_full | Chemistry | 30 | 30.0% | 46.7% | 6 | 1 |
| offr2_final_full | Music | 30 | 33.3% | 23.3% | 2 | 5 |
| offr2_final_full | ALL | 900 | 61.1% | 63.8% | 109 | 85 |

## Question ids per checkpoint

Full model outputs: `runs/<run>/predictions.jsonl` (fields `prediction_raw`, `prediction`, `gold`).

### offr2_final_full / Chemistry
- fixed (W→C): validation_Chemistry_19, validation_Chemistry_25, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_6
- broken (C→W): validation_Chemistry_3
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_17, validation_Chemistry_2, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_7, validation_Chemistry_9

### offr2_final_full / Music
- fixed (W→C): validation_Music_24, validation_Music_30
- broken (C→W): validation_Music_13, validation_Music_23, validation_Music_27, validation_Music_6, validation_Music_9
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_22, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8
