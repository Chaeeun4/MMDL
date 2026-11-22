# Checkpoint report: offpc

Held-out loss (lower is better; `replay` rising = forgetting of the general data).

| step | percept_chem | percept_music | percept_plot | self |
|---|---|---|---|---|
| 0 | 2.661 | 2.178 | 1.924 | 0.357 |
| 200 | 0.053 | 0.070 | 0.042 | 0.177 |
| 400 | 0.036 | 0.041 | 0.025 | 0.165 |
| 600 | 0.031 | 0.034 | 0.023 | 0.161 |
| 638 | 0.031 | 0.034 | 0.023 | 0.161 |

MMMU-val accuracy on the same questions, base model vs checkpoint (30 questions per subject, sampled decoding: a difference of 2-3 questions is within noise).

| checkpoint | subject | n | base | ckpt | W→C | C→W |
|---|---|---|---|---|---|---|
| offpc_final_full | Chemistry | 30 | 30.0% | 40.0% | 4 | 1 |
| offpc_final_full | Music | 30 | 33.3% | 33.3% | 5 | 5 |
| offpc_final_full | ALL | 900 | 61.1% | 63.4% | 101 | 80 |

## Question ids per checkpoint

Full model outputs: `runs/<run>/predictions.jsonl` (fields `prediction_raw`, `prediction`, `gold`).

### offpc_final_full / Chemistry
- fixed (W→C): validation_Chemistry_16, validation_Chemistry_2, validation_Chemistry_22, validation_Chemistry_28
- broken (C→W): validation_Chemistry_21
- still wrong: validation_Chemistry_11, validation_Chemistry_12, validation_Chemistry_13, validation_Chemistry_14, validation_Chemistry_17, validation_Chemistry_19, validation_Chemistry_20, validation_Chemistry_23, validation_Chemistry_25, validation_Chemistry_26, validation_Chemistry_29, validation_Chemistry_30, validation_Chemistry_4, validation_Chemistry_5, validation_Chemistry_6, validation_Chemistry_7, validation_Chemistry_9

### offpc_final_full / Music
- fixed (W→C): validation_Music_14, validation_Music_22, validation_Music_29, validation_Music_3, validation_Music_8
- broken (C→W): validation_Music_13, validation_Music_27, validation_Music_28, validation_Music_6, validation_Music_9
- still wrong: validation_Music_1, validation_Music_11, validation_Music_15, validation_Music_16, validation_Music_17, validation_Music_18, validation_Music_19, validation_Music_2, validation_Music_20, validation_Music_21, validation_Music_24, validation_Music_25, validation_Music_30, validation_Music_4, validation_Music_7
