# Checkpoint report: cm

Held-out loss (lower is better; `replay` rising = forgetting of the general data).

| step | chem_coord | chem_qa | music_qa | music_trans | replay |
|---|---|---|---|---|---|
| 0 | 1.515 | 2.794 | 2.402 | 2.090 | 0.307 |
| 120 | 1.394 | 0.070 | 0.204 | 0.405 | 0.196 |
| 240 | 1.380 | 0.062 | 0.117 | 0.195 | 0.184 |
| 360 | 1.370 | 0.036 | 0.093 | 0.167 | 0.176 |
| 480 | 1.366 | 0.031 | 0.068 | 0.105 | 0.172 |
| 600 | 1.363 | 0.029 | 0.062 | 0.097 | 0.170 |
| 706 | 1.362 | 0.029 | 0.059 | 0.094 | 0.170 |

MMMU-val accuracy on the same questions, base model vs checkpoint (30 questions per subject, sampled decoding: a difference of 2-3 questions is within noise).

| checkpoint | subject | n | base | ckpt | W→C | C→W |
|---|---|---|---|---|---|---|
| cm_step120_cm | Chemistry | 30 | 40.0% | 43.3% | 4 | 3 |
| cm_step120_cm | Music | 30 | 33.3% | 30.0% | 3 | 4 |
| cm_step240_cm | Chemistry | 30 | 40.0% | 50.0% | 7 | 4 |
| cm_step240_cm | Music | 30 | 33.3% | 46.7% | 5 | 1 |
| cm_step360_cm | Chemistry | 30 | 40.0% | 40.0% | 4 | 4 |
| cm_step360_cm | Music | 30 | 33.3% | 30.0% | 2 | 3 |
| cm_step480_cm | Chemistry | 30 | 40.0% | 40.0% | 4 | 4 |
| cm_step480_cm | Music | 30 | 33.3% | 30.0% | 3 | 4 |
| cm_step600_cm | Chemistry | 30 | 40.0% | 56.7% | 7 | 2 |
| cm_step600_cm | Music | 30 | 33.3% | 33.3% | 3 | 3 |
| cm_final_full | Chemistry | 30 | 40.0% | 50.0% | 6 | 3 |
| cm_final_full | Music | 30 | 33.3% | 26.7% | 2 | 4 |
| cm_final_full | ALL | 900 | 63.2% | 63.7% | 94 | 90 |

## Question ids per checkpoint

Full model outputs: `runs/<run>/predictions.jsonl` (fields `prediction_raw`, `prediction`, `gold`).

### cm_step120_cm / Chemistry
- fixed (W→C): validation_Chemistry_2, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_6
- broken (C→W): validation_Chemistry_19, validation_Chemistry_7, validation_Chemistry_9
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_17, validation_Chemistry_20, validation_Chemistry_21, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_29, validation_Chemistry_3, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5

### cm_step120_cm / Music
- fixed (W→C): validation_Music_30, validation_Music_6, validation_Music_9
- broken (C→W): validation_Music_28, validation_Music_29, validation_Music_3, validation_Music_4
- still wrong: validation_Music_1, validation_Music_11, validation_Music_13, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_23, validation_Music_25, validation_Music_27, validation_Music_7, validation_Music_8

### cm_step240_cm / Chemistry
- fixed (W→C): validation_Chemistry_2, validation_Chemistry_21, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_6
- broken (C→W): validation_Chemistry_19, validation_Chemistry_7, validation_Chemistry_8, validation_Chemistry_9
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_17, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_3, validation_Chemistry_4, validation_Chemistry_5

### cm_step240_cm / Music
- fixed (W→C): validation_Music_14, validation_Music_16, validation_Music_23, validation_Music_25, validation_Music_30
- broken (C→W): validation_Music_4
- still wrong: validation_Music_1, validation_Music_11, validation_Music_13, validation_Music_15, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_27, validation_Music_6, validation_Music_7, validation_Music_8, validation_Music_9

### cm_step360_cm / Chemistry
- fixed (W→C): validation_Chemistry_2, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29
- broken (C→W): validation_Chemistry_16, validation_Chemistry_7, validation_Chemistry_8, validation_Chemistry_9
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_17, validation_Chemistry_20, validation_Chemistry_21, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_3, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6

### cm_step360_cm / Music
- fixed (W→C): validation_Music_13, validation_Music_30
- broken (C→W): validation_Music_22, validation_Music_28, validation_Music_4
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_23, validation_Music_25, validation_Music_27, validation_Music_6, validation_Music_7, validation_Music_8, validation_Music_9

### cm_step480_cm / Chemistry
- fixed (W→C): validation_Chemistry_11, validation_Chemistry_2, validation_Chemistry_29, validation_Chemistry_3
- broken (C→W): validation_Chemistry_19, validation_Chemistry_7, validation_Chemistry_8, validation_Chemistry_9
- still wrong: validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_17, validation_Chemistry_20, validation_Chemistry_21, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6

### cm_step480_cm / Music
- fixed (W→C): validation_Music_14, validation_Music_27, validation_Music_9
- broken (C→W): validation_Music_24, validation_Music_29, validation_Music_3, validation_Music_4
- still wrong: validation_Music_1, validation_Music_11, validation_Music_13, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_23, validation_Music_25, validation_Music_30, validation_Music_6, validation_Music_7, validation_Music_8

### cm_step600_cm / Chemistry
- fixed (W→C): validation_Chemistry_11, validation_Chemistry_2, validation_Chemistry_20, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30
- broken (C→W): validation_Chemistry_7, validation_Chemistry_9
- still wrong: validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_17, validation_Chemistry_21, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_3, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6

### cm_step600_cm / Music
- fixed (W→C): validation_Music_14, validation_Music_30, validation_Music_9
- broken (C→W): validation_Music_12, validation_Music_28, validation_Music_3
- still wrong: validation_Music_1, validation_Music_11, validation_Music_13, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_23, validation_Music_25, validation_Music_27, validation_Music_6, validation_Music_7, validation_Music_8

### cm_final_full / Chemistry
- fixed (W→C): validation_Chemistry_11, validation_Chemistry_14, validation_Chemistry_2, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30
- broken (C→W): validation_Chemistry_16, validation_Chemistry_7, validation_Chemistry_9
- still wrong: validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_17, validation_Chemistry_20, validation_Chemistry_21, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_26, validation_Chemistry_3, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6

### cm_final_full / Music
- fixed (W→C): validation_Music_30, validation_Music_9
- broken (C→W): validation_Music_28, validation_Music_29, validation_Music_3, validation_Music_4
- still wrong: validation_Music_1, validation_Music_11, validation_Music_13, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_23, validation_Music_25, validation_Music_27, validation_Music_6, validation_Music_7, validation_Music_8
