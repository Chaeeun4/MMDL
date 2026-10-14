# Evidence pack for the proposal

- 01_headline_numbers.md: baseline facts, seed-noise, symbolic-image subset, by image type
- 02_compare_table.md: every run vs baseline on the same questions (W→C/C→W, McNemar p)
- 03_by_image_type.md: per-image-type accuracy for every run
- 04_examples/: one folder per example question: prompt, gold, explanation, every run's response, image PNGs
- 05_run_metadata/: metrics/manifest/command of every run (settings, versions, timing, VRAM)
- 06_length_stops.md: which questions hit the 32768-token limit in which run

Examples chosen: baseline answered in <=10 tokens and wrong; a diagnostic run got it right. 8 picked.
