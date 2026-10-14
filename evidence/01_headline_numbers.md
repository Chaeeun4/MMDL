# Headline numbers (baseline run)

- MMMU validation: **550/900 = 61.1%** (macro over subjects = micro, 30 q/subject)
- multiple-choice: 541/847 = 63.9%
- open: 9/53 = 17.0%
- finish_reason: {'stop': 860, 'length': 40}; length-stops by subject: {'Mechanical_Engineering': 8, 'Energy_and_Power': 7, 'Materials': 7, 'Accounting': 5, 'Architecture_and_Engineering': 5, 'Finance': 2}
- completion tokens: mean 2384, median 8; correct mean 1400 vs wrong mean 3932
- seed-only rerun: 541/900 = 60.1%, 59 questions flipped (6.6% of questions)

## Symbolic-image subset (Sheet Music / Chemical Structures / Sketches and Drafts / Technical Blueprints)

- n=95, correct 31 = 32.6%; random-guess expectation 25.0%
- answered in <=10 tokens: 63 (66.3%), accuracy of those 33.3%
- MC wrong answers with first-token prob >= 0.9 (confidently wrong): 16 of 56
- Sheet Music: n=30, acc 33.3%, median visual tokens 192, <=10-token answers 28
- Chemical Structures: n=31, acc 29.0%, median visual tokens 80, <=10-token answers 15
- Sketches and Drafts: n=14, acc 28.6%, median visual tokens 494, <=10-token answers 9
- Technical Blueprints: n=20, acc 40.0%, median visual tokens 144, <=10-token answers 11

## Accuracy by image type (all 900)

| img_type | n | acc |
|---|---|---|
| Sketches and Drafts | 14 | 28.6% |
| Chemical Structures | 31 | 29.0% |
| Sheet Music | 30 | 33.3% |
| Technical Blueprints | 20 | 40.0% |
| Trees and Graphs | 12 | 41.7% |
| Microscopic Images | 29 | 51.7% |
| Portraits | 13 | 53.8% |
| Pathological Images | 26 | 53.8% |
| Diagrams | 246 | 60.2% |
| Plots and Charts | 82 | 61.0% |
| Maps | 13 | 61.5% |
| Medical Images | 32 | 62.5% |
| Body Scans: MRI, CT scans, and X-rays | 17 | 64.7% |
| Photographs | 87 | 65.5% |
| Paintings | 53 | 66.0% |
| Comics and Cartoons | 24 | 66.7% |
| Tables | 171 | 73.7% |
| Geometric Shapes | 20 | 75.0% |
