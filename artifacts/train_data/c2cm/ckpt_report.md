# Checkpoint report: c2cm

Held-out loss (lower is better; `replay` rising = forgetting of the general data).

| step | chem_coord | chem_qa | music_qa | music_trans | replay |
|---|---|---|---|---|---|
| 0 | 1.515 | 2.797 | 2.390 | 2.061 | 0.541 |
| 120 | 1.399 | 0.057 | 0.184 | 0.357 | 0.341 |
| 240 | 1.378 | 0.045 | 0.126 | 0.220 | 0.323 |
| 360 | 1.369 | 0.039 | 0.085 | 0.148 | 0.310 |
| 480 | 1.363 | 0.032 | 0.068 | 0.121 | 0.305 |
| 600 | 1.361 | 0.027 | 0.060 | 0.100 | 0.299 |
| 720 | 1.360 | 0.027 | 0.057 | 0.094 | 0.299 |
| 776 | 1.361 | 0.027 | 0.056 | 0.094 | 0.299 |

MMMU-val accuracy on the same questions, base model vs checkpoint (30 questions per subject, sampled decoding: a difference of 2-3 questions is within noise).

| checkpoint | subject | n | base | ckpt | W→C | C→W |
|---|---|---|---|---|---|---|
| c2cm_step120_cm | Chemistry | 30 | 30.0% | 33.3% | 2 | 1 |
| c2cm_step120_cm | Music | 30 | 33.3% | 30.0% | 1 | 2 |
| c2cm_step240_cm | Chemistry | 30 | 30.0% | 36.7% | 3 | 1 |
| c2cm_step240_cm | Music | 30 | 33.3% | 33.3% | 2 | 2 |
| c2cm_step360_cm | Chemistry | 30 | 30.0% | 26.7% | 2 | 3 |
| c2cm_step360_cm | Music | 30 | 33.3% | 30.0% | 2 | 3 |
| c2cm_step480_cm | Chemistry | 30 | 30.0% | 33.3% | 2 | 1 |
| c2cm_step480_cm | Music | 30 | 33.3% | 30.0% | 2 | 3 |
| c2cm_step600_cm | Chemistry | 30 | 30.0% | 33.3% | 2 | 1 |
| c2cm_step600_cm | Music | 30 | 33.3% | 33.3% | 2 | 2 |
| c2cm_step720_cm | Chemistry | 30 | 30.0% | 26.7% | 1 | 2 |
| c2cm_step720_cm | Music | 30 | 33.3% | 30.0% | 2 | 3 |
| c2cm_final_full | Chemistry | 30 | 30.0% | 30.0% | 1 | 1 |
| c2cm_final_full | Music | 30 | 33.3% | 30.0% | 2 | 3 |
| c2cm_final_full | ALL | 900 | 61.1% | 59.7% | 42 | 55 |

## Question ids per checkpoint

Full model outputs: `runs/<run>/predictions.jsonl` (fields `prediction_raw`, `prediction`, `gold`).

### c2cm_step120_cm / Chemistry
- fixed (W→C): validation_Chemistry_2, validation_Chemistry_26
- broken (C→W): validation_Chemistry_3
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_17, validation_Chemistry_19, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### c2cm_step120_cm / Music
- fixed (W→C): validation_Music_30
- broken (C→W): validation_Music_28, validation_Music_6
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8

### c2cm_step240_cm / Chemistry
- fixed (W→C): validation_Chemistry_17, validation_Chemistry_2, validation_Chemistry_26
- broken (C→W): validation_Chemistry_21
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_19, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### c2cm_step240_cm / Music
- fixed (W→C): validation_Music_21, validation_Music_30
- broken (C→W): validation_Music_28, validation_Music_6
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8

### c2cm_step360_cm / Chemistry
- fixed (W→C): validation_Chemistry_17, validation_Chemistry_2
- broken (C→W): validation_Chemistry_21, validation_Chemistry_3, validation_Chemistry_8
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_19, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### c2cm_step360_cm / Music
- fixed (W→C): validation_Music_21, validation_Music_30
- broken (C→W): validation_Music_28, validation_Music_6, validation_Music_9
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8

### c2cm_step480_cm / Chemistry
- fixed (W→C): validation_Chemistry_17, validation_Chemistry_2
- broken (C→W): validation_Chemistry_21
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_19, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### c2cm_step480_cm / Music
- fixed (W→C): validation_Music_21, validation_Music_30
- broken (C→W): validation_Music_28, validation_Music_6, validation_Music_9
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8

### c2cm_step600_cm / Chemistry
- fixed (W→C): validation_Chemistry_2, validation_Chemistry_26
- broken (C→W): validation_Chemistry_3
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_17, validation_Chemistry_19, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### c2cm_step600_cm / Music
- fixed (W→C): validation_Music_21, validation_Music_30
- broken (C→W): validation_Music_28, validation_Music_6
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8

### c2cm_step720_cm / Chemistry
- fixed (W→C): validation_Chemistry_2
- broken (C→W): validation_Chemistry_21, validation_Chemistry_3
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_17, validation_Chemistry_19, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### c2cm_step720_cm / Music
- fixed (W→C): validation_Music_21, validation_Music_30
- broken (C→W): validation_Music_28, validation_Music_6, validation_Music_9
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8

### c2cm_final_full / Chemistry
- fixed (W→C): validation_Chemistry_17
- broken (C→W): validation_Chemistry_21
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_16, validation_Chemistry_19, validation_Chemistry_2, validation_Chemistry_20, validation_Chemistry_22, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_26, validation_Chemistry_28, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### c2cm_final_full / Music
- fixed (W→C): validation_Music_21, validation_Music_30
- broken (C→W): validation_Music_28, validation_Music_6, validation_Music_9
- still wrong: validation_Music_1, validation_Music_11, validation_Music_14, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_22, validation_Music_24, validation_Music_25, validation_Music_29, validation_Music_3, validation_Music_4, validation_Music_7, validation_Music_8
