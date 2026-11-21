# MMMU Music·Chemistry 오답 분석

## 요약

- 같은 60문항에서 Base → PrIMuS step 500은 24→29점이었다. 12개를 새로 맞히고 7개를 새로 틀렸다.
- PrIMuS step 500의 900문항 재실행에서는 같은 60문항이 22점이었다. 60문항 최고점의 재현성을 먼저 확인할 필요가 있다.
- C1과 CM의 묘사 프롬프트 결과는 모두 23/60이었다. CM은 Music에서 3문제 줄고 Chemistry에서 3문제 늘었다.
- 공식 프롬프트의 CM → C2CM은 550→537/900이었다. 순감소 13개 중 11개가 Music·Chemistry 밖에서 나왔다.

## 비교 방법

`main` 391ab34의 저장 예측과 `origin/jina` 6289df4의 저장 예측을 문항 ID로 맞추고 정답과 과목이 일치하는지 검사했다. `code/compare_runs.py`의 비교 함수로 정오 전환과 exact McNemar p를 계산했다. 자동 집계에는 저장된 채점 결과를 사용했다.

Base 60, PrIMuS 60, PubChem 750, 혼합 1688, PrIMuS 900은 `legacy_cot`이며, PrIMuS 묘사는 같은 step 500의 `describe_cot`이다. C1과 CM 묘사, CM 240은 `describe_cot`이고, CM 공식과 C2CM, Jina Base 및 seed 1234는 `official`이다. 괄호의 ↑는 오답→정답, ↓는 정답→오답이다.

## 정량 비교

| 비교 | Music | Chemistry | M+C | McNemar p (M+C) |
|---|---:|---:|---:|---:|
| Base 60 → PrIMuS 60 | 9→12/30 (6↑·3↓) | 15→17/30 (6↑·4↓) | 24→29/60 (12↑·7↓) | 0.359 |
| Base 60 → PubChem 750 | 9→12/30 (5↑·2↓) | 15→14/30 (3↑·4↓) | 24→26/60 (8↑·6↓) | 0.791 |
| Base 60 → 혼합 1688 | 9→13/30 (7↑·3↓) | 15→14/30 (5↑·6↓) | 24→27/60 (12↑·9↓) | 0.664 |
| PrIMuS 60 → PrIMuS 묘사 | 12→7/30 (3↑·8↓) | 17→14/30 (3↑·6↓) | 29→21/60 (6↑·14↓) | 0.115 |
| PrIMuS 60 → PrIMuS 900 | 12→9/30 (2↑·5↓) | 17→13/30 (0↑·4↓) | 29→22/60 (2↑·9↓) | 0.065 |
| Jina Base 묘사 → CM 240 | 10→14/30 (5↑·1↓) | 12→15/30 (7↑·4↓) | 22→29/60 (12↑·5↓) | 0.143 |
| C1 → CM 묘사 | 11→8/30 (2↑·5↓) | 12→15/30 (6↑·3↓) | 23→23/60 (8↑·8↓) | 1.000 |
| CM 공식 → C2CM | 8→9/30 (2↑·1↓) | 12→9/30 (2↑·5↓) | 20→18/60 (4↑·6↓) | 0.754 |
| Jina Base → Jina seed 1234 | 10→8/30 (0↑·2↓) | 9→8/30 (1↑·2↓) | 19→16/60 (1↑·4↓) | 0.375 |

동일한 900문항 전체에서도 비교 가능한 실행은 아래와 같다.

| 비교 | 전체 | McNemar p |
|---|---:|---:|
| Jina Base 묘사 → C1 | 569→572/900 (101↑·98↓) | 0.887 |
| Jina Base 묘사 → CM 묘사 | 569→573/900 (94↑·90↓) | 0.825 |
| C1 → CM 묘사 | 572→573/900 (87↑·86↓) | 1.000 |
| CM 공식 → C2CM | 550→537/900 (44↑·57↓) | 0.232 |
| Jina Base → Jina seed 1234 | 550→541/900 (25↑·34↓) | 0.298 |

## 유형별 정오 변화

유형은 `origin/jina:experiments/cm_ft/README.md`의 문항 번호 분류를 적용했다. Music의 평가 메타데이터는 전부 Sheet Music이라 이 분류가 세부 유형을 보는 데 필요하다. 표는 문항 유형별 정오 집계이며 모델이 틀린 원인에는 원문 검토가 필요하다.

| 과목 | 문항 유형 | n | Base → PrIMuS | C1 → CM 묘사 | CM 공식 → C2CM |
|---|---|---:|---:|---:|---:|
| Music | 음이름·음정·음계 판독 | 9 | 3→6/9 (3↑·0↓) | 4→3/9 (0↑·1↓) | 1→3/9 (2↑·0↓) |
| Music | 리듬·박자 | 8 | 2→4/8 (3↑·1↓) | 3→0/8 (0↑·3↓) | 2→2/8 (0↑·0↓) |
| Music | 화음·화성 | 5 | 1→0/5 (0↑·1↓) | 2→3/5 (1↑·0↓) | 1→0/5 (0↑·1↓) |
| Music | 조성·음계·전조 | 4 | 2→2/4 (0↑·0↓) | 1→1/4 (1↑·1↓) | 2→2/4 (0↑·0↓) |
| Music | 총보·꾸밈음 | 4 | 1→0/4 (0↑·1↓) | 1→1/4 (0↑·0↓) | 2→2/4 (0↑·0↓) |
| Chemistry | 입체화학 | 9 | 2→3/9 (3↑·2↓) | 1→3/9 (3↑·1↓) | 1→1/9 (1↑·1↓) |
| Chemistry | 그래프·도표 판독 | 6 | 4→4/6 (0↑·0↓) | 2→3/6 (1↑·0↓) | 3→2/6 (0↑·1↓) |
| Chemistry | 표·그림 값으로 계산 | 5 | 4→4/5 (0↑·0↓) | 4→4/5 (0↑·0↓) | 3→3/5 (0↑·0↓) |
| Chemistry | 루이스 구조·분자 모양 | 4 | 2→3/4 (2↑·1↓) | 2→2/4 (1↑·1↓) | 1→0/4 (0↑·1↓) |
| Chemistry | 유기 반응성·성질 | 4 | 2→2/4 (1↑·1↓) | 2→1/4 (0↑·1↓) | 2→1/4 (1↑·2↓) |
| Chemistry | 생화학·당 분류 | 2 | 1→1/2 (0↑·0↓) | 1→2/2 (1↑·0↓) | 2→2/2 (0↑·0↓) |

## 길이 종료와 파싱 진단

길이 종료는 `finish_reason=length`로 집계했다. 파싱 결과 없음은 `null` 또는 빈 리스트이며, 정답 표시가 틀린 위치에서 추출된 경우는 원문을 확인해야 한다. 두 지표는 같은 문항에 동시에 발생할 수 있다.

| 실행 | Music 길이 종료 / 그중 오답 / 파싱 없음 | Chemistry 길이 종료 / 그중 오답 / 파싱 없음 |
|---|---:|---:|
| Base 60 | 14 / 12 / 1 | 4 / 2 / 0 |
| PrIMuS 60 | 10 / 9 / 3 | 3 / 1 / 0 |
| PrIMuS 묘사 | 11 / 9 / 3 | 4 / 1 / 2 |
| PubChem 750 | 6 / 3 / 0 | 3 / 2 / 0 |
| 혼합 1688 | 3 / 2 / 1 | 0 / 0 / 0 |
| PrIMuS 900 | 8 / 7 / 0 | 2 / 1 / 0 |
| Base 1005 | 11 / 7 / 0 | 7 / 4 / 0 |
| Jina Base | 0 / 0 / 0 | 1 / 1 / 0 |
| Jina Base 묘사 | 13 / 10 / 0 | 6 / 3 / 0 |
| Jina seed 1234 | 1 / 1 / 0 | 1 / 0 / 0 |
| C1 | 1 / 1 / 0 | 0 / 0 / 1 |
| CM 240 | 2 / 2 / 2 | 0 / 0 / 0 |
| CM 묘사 | 3 / 3 / 1 | 1 / 1 / 0 |
| CM 공식 | 2 / 2 / 0 | 0 / 0 / 0 |
| C2CM | 0 / 0 / 0 | 0 / 0 / 0 |

## Base → PrIMuS의 정오 전환 문항

아래 원문은 답변 끝부분이며, 종료 이유와 파싱된 답을 함께 표시했다.

| 문항 | 정답 | 기준 답 / 종료 | 비교 답 / 종료 | 변화 | 답변 끝부분 (기준 → 비교) |
|---|---|---|---|---|---|
| Chemistry_3 | C | C / stop | A / stop | 정답→오답 | ...is the answer. Perhaps that’s it. I think the intended answer is (C). So I’ll go with (C). ANSWER: C → ...he incorrect statement is (A) because the product is not aromatic; it's an ionic compound. ANSWER: A |
| Chemistry_7 | C | C / length | D / length | 정답→오답 | ...ps the diagram is showing a molecule with a different connectivity. Wait, perhaps the structure is 2 → ... Perhaps the structure is CH3-C(Br)(H)-CH2-C(Br)(H)-CH3 — and there are two chiral centers. But 4 is |
| Chemistry_12 | A | A / length | C / stop | 정답→오답 | ...nd Et is attached to the same carbon? That doesn't work. Perhaps "Me" and "Et" are not both attached → ...tion (C) is the correct answer as it represents the mirror image of the original compound. ANSWER: C |
| Chemistry_14 | B | A / stop | B / stop | 오답→정답 | ...reference: Morphine has 4 chiral centers (excluding nitrogen). Therefore, the answer is 4. ANSWER: A → ...wer is 5. The structure shows 5 carbon atoms that are chiral centers (excluding nitrogen). ANSWER: B |
| Chemistry_16 | D | D / stop | E / stop | 정답→오답 | ... there are four bonds and no lone pairs, it’s tetrahedral. Yes, so I think (D) is correct. ANSWER: D → ...nd sulfur, the shape is square planar. Therefore, the correct answer is (E) square planar. ANSWER: E |
| Chemistry_17 | B | C / stop | B / stop | 오답→정답 | ...ommon knowledge. Upon checking, the correct answer is R and S. So, the answer is (C) R, S. ANSWER: C → ...s also gives a plane of symmetry. 6) Therefore, the correct answer should include P and R. ANSWER: B |
| Chemistry_19 | 4 | ['a carbon atom bonded to four different groups.', 'bonded t / length | ['bonded to four different groups:', 'a branched alkyl group / length | 오답→정답 | ...t right. The structure is: The carbon Cβ is bonded to: - H - CH₃ - CH₂ - CH₃ But CH₂ is bonded to CH → ... so it is chiral. So isoleucine has two chiral centers — so 4 stereoisomers — 2 optical isomers. But |
| Chemistry_21 | B | D / stop | B / stop | 오답→정답 | ...sider the hydroxyl oxygen to be in the plane — but it’s not. I think I have to choose (D). ANSWER: D → ...he only one that mentions planarity, and the carboxyl group is planar. So I’ll choose (B). ANSWER: B |
| Chemistry_26 | C | A / stop | C / length | 오답→정답 | ...tually, no — it's definitely wrong. Perhaps the answer is C. But I think I will go with A. ANSWER: A → ...erhaps it’s **diazine** — which is a 4-membered ring with two nitrogens — and a double bond — that’s |
| Chemistry_30 | ['$MgS$', 'MgS'] | ['mx'] / stop | ['mgs'] / stop | 오답→정답 | ... X are (as long as they are third-period elements forming these ions), the formula is MX. ANSWER: MX → ... M is likely magnesium (Mg), and X is sulfur (S). Therefore, the compound formed is MgS. ANSWER: MgS |
| Music_3 | B | A / stop | B / stop | 오답→정답 | ...e treble note is G, the interval is a perfect fifth. Therefore, the answer is (A) perfect. ANSWER: A → ...that is not perfect, diminished, or augmented. Therefore, the correct answer is (B) major. ANSWER: B |
| Music_8 | B | B / length | A / length | 정답→오답 | ...as a “b°8” — but that’s not a note — it’s a chord symbol. Wait — perhaps the chord symbol is “b°8” — → ...? No, it's clearly G4. Wait, maybe I should consider the note on the treble clef as G4 (which is the |
| Music_12 | A | A / stop | None / length | 정답→오답 | ...e quietest bar. Therefore, the statement "Bar 8 is the quietest bar in the music" is true. ANSWER: A → .... Since bar 9 is also quiet, bar 8 is not the quietest. Wait — I think I need to reconsider. Looking |
| Music_13 | C | B / stop | C / stop | 오답→정답 | ...(B) AD is one of them. Perhaps the intended answer is (B) AD. I think I'll go with (B) AD. ANSWER: B → ...ink the intended answer is C — because 6/8 is more standard than 3/4. So I will go with C. ANSWER: C |
| Music_14 | B | C / length | B / stop | 오답→정답 | ...I need to accept that A to C is a major third, and since it’s less than an octave, it’s not compound → ...h the options. The correct option is "compound major 3rd". Therefore, the answer is box 2. ANSWER: B |
| Music_19 | B | D / stop | B / stop | 오답→정답 | ...lets of eighth notes — each triplet equals one beat — total two beats — matching 2/4 time. ANSWER: D → ...ts. This matches the definition of 2/4 time signature. Therefore, the correct answer is B. ANSWER: B |
| Music_20 | D | D / length | C / length | 정답→오답 | ... the time signature is 4/4 — but the “4” above the barline is indicating a different time signature? → ... The note D5 is played next. The note D5 is played on a rest. The note C5 is played next. The note C |
| Music_23 | C | B / length | C / stop | 오답→정답 | ...at's not right. Actually, in 3/4 time, a quarter note is 1 beat, so a half note is 2 beats, which is → ...sixth note (.) - this matches the original bar. Therefore, the correct answer is option C. ANSWER: C |
| Music_25 | B | D / length | B / stop | 오답→정답 | ...emitones — which is a minor 3rd? But that’s not right — because in the chromatic scale, from B♭ to E → ...the correct option. Since the interval is a major second, the correct answer is (B) major. ANSWER: B |

## PrIMuS 60q → 900q 재실행의 정오 전환 문항

아래 원문은 답변 끝부분이며, 종료 이유와 파싱된 답을 함께 표시했다.

| 문항 | 정답 | 기준 답 / 종료 | 비교 답 / 종료 | 변화 | 답변 끝부분 (기준 → 비교) |
|---|---|---|---|---|---|
| Chemistry_6 | B | B / stop | E / stop | 정답→오답 | ...nt. (E) 7 and 8 — 7 is on the boundary, 8 is on the other curve. So, the best answer is B. ANSWER: B → ...reezing equilibrium. Therefore, points 7 and 8 correspond to melting/freezing equilibrium. ANSWER: E |
| Chemistry_11 | B | B / stop | D / stop | 정답→오답 | ...match. Therefore, the correct answer is (B): A strong acid is titrated into a strong base. ANSWER: B → ...(D) "A strong base is titrated into a strong acid" best matches the titration curve shown. ANSWER: D |
| Chemistry_17 | B | B / stop | D / stop | 정답→오답 | ...s also gives a plane of symmetry. 6) Therefore, the correct answer should include P and R. ANSWER: B → ...e, for meso-2,3-butanediol, the correct Newman projections are Q and S. So I'll go with D. ANSWER: D |
| Chemistry_21 | B | B / stop | A / stop | 정답→오답 | ...he only one that mentions planarity, and the carboxyl group is planar. So I’ll choose (B). ANSWER: B → ...is (A) — and the structure is drawn with the alpha carbon in a plane. So I'll go with (A). ANSWER: A |
| Music_2 | A | A / length | B / stop | 정답→오답 | ...e. Wait — perhaps the note after C5 is D5? But the note shown is Bb5? No — I think I need to look at → ...e, the statement “This is the correctly written chromatic scale beginning on Bb” is FALSE. ANSWER: B |
| Music_12 | A | None / length | A / stop | 오답→정답 | .... Since bar 9 is also quiet, bar 8 is not the quietest. Wait — I think I need to reconsider. Looking → ...p" is the most quiet dynamic marking shown in the score, bar 8 is indeed the quietest bar. ANSWER: A |
| Music_13 | C | C / stop | D / stop | 정답→오답 | ...ink the intended answer is C — because 6/8 is more standard than 3/4. So I will go with C. ANSWER: C → .../4 (standard) and 12/8 (standard) → both are standard. Therefore, the correct answer is D. ANSWER: D |
| Music_16 | B | B / stop | D / stop | 정답→오답 | ...otted duration — because it's not even a dotted rest. So the correct answer should be (B). ANSWER: B → ...s a rest that does not have a compound dotted duration. Therefore, the answer should be D. ANSWER: D |
| Music_22 | A | B / length | A / length | 오답→정답 | ...Let me try to think about the note again. The note shown is G4. In G Major, the notes are G, B, D, F → ...n the key of A major would be A7, which is made up of A4, C#5, E5, G#5. So if the note shown is G#4, |
| Music_25 | B | B / stop | A / stop | 정답→오답 | ...the correct option. Since the interval is a major second, the correct answer is (B) major. ANSWER: B → ... the correct option based on the type of interval. A perfect fourth is a perfect interval. ANSWER: A |
| Music_30 | A | A / stop | B / stop | 정답→오답 | ...1: The note sequence fits with C minor. Therefore, the correct answer is the first option. ANSWER: A → ...nd fits the tonal structure. Therefore, the correct answer is to circle the second option. ANSWER: B |

## 해석과 다음 실험

1. **60q 최고점 재현.** PrIMuS step 500과 Base를 같은 이미지 처리·프롬프트·평가 코드·문항 순서로 다시 돌린다. seed 3407과 1234를 포함한 동일한 seed 목록을 짝지어 사용한다. 60q와 900q는 평가 범위가 다르고 저장본에 렌더링된 프롬프트가 없어, 결과 차이의 원인은 이 예측 파일만으로 확정할 수 없다.
2. **변화 문항 원인 라벨링.** 위 표의 원문 전체와 이미지를 나란히 보고 이미지 판독, 지식·추론, 최종 답 출력, 파싱, 길이 종료로 기록한다. 예를 들어 `Chemistry_28`은 Jina 문서가 선택지 문구에 포함된 문자 때문에 답이 잘못 파싱된 사례로 기록했다. 현재 표에는 저장된 채점을 사용했고 이 건을 수동 보정하지 않았다.
3. **결과 선택 효과.** 60q에서 여러 step과 프롬프트를 고른 뒤 같은 60q 점수로 순위를 매겼으므로 McNemar p는 탐색적 비교로 읽는다. 기존 900q Base 재채점의 16K 컨텍스트와 저장된 PrIMuS·PubChem 결과의 해상도 차이도 별도로 기록한다.

## Replay 양을 맞춘다는 뜻

Replay는 화학·음악 과제에 섞어 다시 학습시키는 일반 멀티모달 풀이 데이터다. 빌드 기록에서 CM은 replay **3,893개 / 전체 11,307개**, C2CM은 replay **5,006개 / 전체 12,419개**였다. 음악 전사도 914개와 913개로 달랐고, 학습 업데이트는 각각 706회와 776회였다.

교사 풀이의 효과를 확인하는 실험은 두 학습에 동일한 도메인 샘플과 replay 총량을 사용한다. 예를 들어 각각 replay 3,893개를 사용하고, 한쪽의 일부 자체 풀이를 같은 질문에 대한 Claude 풀이로 교체한다. 가능한 범위에서 풀이 길이 분포와 학습 토큰 예산·업데이트 수를 맞추고, 같은 평가 프롬프트·seed로 비교한다. 공통 문항에 대한 풀이 품질 비교와 교사가 더 어려운 문항을 추가로 커버하는 효과를 따로 보고 싶으면, 후자는 별도 조건으로 평가한다.

### 자료

- [실험 정리](/home/cepark/Desktop/exp정리)
- [정오 전환 집계 코드](../../code/compare_runs.py), [과목별 분석 코드](../../code/analyze_subject_errors.py), [문항별 오답 시트 코드](../../code/error_sheet.py)
- Jina 문항 유형과 replay 구성은 `origin/jina:experiments/cm_ft/README.md` 및 CM·C2CM의 `build_stats.json` 참조.
