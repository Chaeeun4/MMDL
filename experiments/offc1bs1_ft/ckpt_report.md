# Checkpoint report: offc1bs1

Held-out loss (lower is better; `replay` rising = forgetting of the general data).

| step | self |
|---|---|
| 0 | 0.357 |
| 200 | 0.158 |
| 243 | 0.157 |

MMMU-val accuracy on the same questions, base model vs checkpoint (30 questions per subject, sampled decoding: a difference of 2-3 questions is within noise).

| checkpoint | subject | n | base | ckpt | W→C | C→W |
|---|---|---|---|---|---|---|
| offc1bs1_final_full | Chemistry | 30 | 30.0% | 46.7% | 7 | 2 |
| offc1bs1_final_full | Music | 30 | 33.3% | 36.7% | 5 | 4 |
| offc1bs1_final_full | ALL | 900 | 61.1% | 63.2% | 100 | 81 |

## Question ids per checkpoint

Full model outputs: `runs/<run>/predictions.jsonl` (fields `prediction_raw`, `prediction`, `gold`).

### offc1bs1_final_full / Chemistry
- fixed (W→C): validation_Chemistry_12, validation_Chemistry_16, validation_Chemistry_19, validation_Chemistry_2, validation_Chemistry_25, validation_Chemistry_5, validation_Chemistry_6
- broken (C→W): validation_Chemistry_3, validation_Chemistry_8
- still wrong: validation_Chemistry_11, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_17, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_7, validation_Chemistry_9

### offc1bs1_final_full / Music
- fixed (W→C): validation_Music_14, validation_Music_2, validation_Music_3, validation_Music_30, validation_Music_4
- broken (C→W): validation_Music_23, validation_Music_26, validation_Music_27, validation_Music_28
- still wrong: validation_Music_1, validation_Music_11, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_20, validation_Music_21, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_7, validation_Music_8
