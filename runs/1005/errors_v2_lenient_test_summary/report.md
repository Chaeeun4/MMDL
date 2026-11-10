# MMMU 오답 분석 리포트

## 1. 실행 정보

- 생성 시각: 2026-10-06T01:34:08
- 입력 로그: `./runs/1005/predictions.jsonl` / 분류 결과: `./runs/1005/errors_v2_lenient_test.jsonl`
- 분류 모델: gpt-5.4-mini, rule / 프롬프트 버전: v2
- 전체 900문제, 정확도 64.44%, 오답 320개
- 직답 기준: 응답 20토큰 이하 (판단할 증거가 없어 LLM 분류에서 제외, direct_answer)

## 2. 오답 유형 (pct_of_all_questions = 정확도에 환산했을 때의 %p)

| category | count | percent_of_errors | pct_of_all_questions |
|---|---|---|---|
| reasoning | 178 | 55.6 | 19.78 |
| truncation | 73 | 22.8 | 8.11 |
| knowledge | 23 | 7.2 | 2.56 |
| grading_mismatch | 21 | 6.6 | 2.33 |
| perception | 20 | 6.2 | 2.22 |
| calculation | 4 | 1.2 | 0.44 |
| question_issue | 1 | 0.3 | 0.11 |

## 3. 응답 유형별 (direct=직답 / cot=풀이 있음 / truncated=잘림)

| category | cot | truncated | All |
|---|---|---|---|
| calculation | 4 | 0 | 4 |
| grading_mismatch | 21 | 0 | 21 |
| knowledge | 23 | 0 | 23 |
| perception | 20 | 0 | 20 |
| question_issue | 1 | 0 | 1 |
| reasoning | 178 | 0 | 178 |
| truncation | 0 | 73 | 73 |
| All | 247 | 73 | 320 |

## 4. 하위 유형 (LLM 분류분만)

### reasoning (178개)

| subtype | count | percent |
|---|---|---|
| misread_condition | 88 | 49.4 |
| option_mapping | 35 | 19.7 |
| wrong_method | 29 | 16.3 |
| logic_error | 11 | 6.2 |
| unspecified | 6 | 3.4 |
| late_revision | 6 | 3.4 |
| skipped_step | 3 | 1.7 |

### perception (20개)

| subtype | count | percent |
|---|---|---|
| structure_relation | 8 | 40.0 |
| object_recognition | 5 | 25.0 |
| value_reading | 3 | 15.0 |
| text_ocr | 2 | 10.0 |
| symbol_notation | 1 | 5.0 |
| counting_spatial | 1 | 5.0 |

### knowledge: 부족한 개념 상위 (개념이 몰려 있으면 구체적 갭, 흩어져 있으면 전반적 갭)

상위 10개 개념이 차지하는 비율: 43.5% (개념 23개 중)

| missing_concept | count |
|---|---|
| ash bacterial disease | 1 |
| phytoplasma symptoms | 1 |
| algae appearance on leaves | 1 |
| downy mildew infection conditions | 1 |
| standard architectural symbol conventions | 1 |
| artist attribution for william hunter portrait | 1 |
| egg tempera | 1 |
| location of a conversation with the sea | 1 |
| hagia sophia interior mosaics | 1 |
| h+-coupled amino acid transport | 1 |
| morphine chiral center count | 1 |
| third-period element identification from lewis structures | 1 |
| micronesian navigation charts record ocean currents and landforms | 1 |
| lewy body immunostains | 1 |
| hydromyelia vs syringomyelia distinction | 1 |

## 5. 모호성 분석 (second_guess, confidence)

- LLM 분류 247개 중 차선 유형이 있는 것: 219개 (88.7%), confidence<=2: 6개, 둘 중 하나라도 해당: 219개 (88.7%)
- 많이 헷갈리는 쌍은 카테고리 정의가 모호하다는 신호입니다. 정의를 고치거나 한 칸으로 합쳐 보세요.

| primary | second_guess | count |
|---|---|---|
| reasoning | knowledge | 131 |
| reasoning | perception | 26 |
| knowledge | reasoning | 22 |
| perception | reasoning | 19 |
| grading_mismatch | reasoning | 6 |
| reasoning | other | 4 |
| reasoning | calculation | 3 |
| calculation | reasoning | 3 |
| calculation | question_issue | 1 |
| grading_mismatch | calculation | 1 |

- 보고서의 주 집계는 primary 하나를 쓰고, second_guess는 모호성 지표와 검수 대상 선정에만 씁니다.

## 6. 유형별 오답 구성 (n이 작은 행(*)은 해석 주의)

### img_type

| index | calculation | grading_mismatch | knowledge | perception | question_issue | reasoning | truncation |
|---|---|---|---|---|---|---|---|
| Body Scans: MRI, CT scans, and X-rays* (n=6) | 0.0 | 0.0 | 0.0 | 16.7 | 0.0 | 83.3 | 0.0 |
| Chemical Structures (n=18) | 0.0 | 0.0 | 11.1 | 22.2 | 0.0 | 50.0 | 16.7 |
| Comics and Cartoons* (n=8) | 0.0 | 25.0 | 0.0 | 0.0 | 0.0 | 75.0 | 0.0 |
| Diagrams (n=103) | 1.0 | 10.7 | 3.9 | 3.9 | 0.0 | 48.5 | 32.0 |
| Geometric Shapes* (n=8) | 0.0 | 12.5 | 12.5 | 12.5 | 0.0 | 12.5 | 50.0 |
| Logos and Branding* (n=1) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 |
| Maps* (n=4) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 75.0 | 25.0 |
| Mathematical Notations* (n=1) | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| Medical Images (n=12) | 0.0 | 0.0 | 8.3 | 16.7 | 0.0 | 66.7 | 8.3 |
| Microscopic Images (n=12) | 0.0 | 0.0 | 16.7 | 8.3 | 8.3 | 66.7 | 0.0 |
| Other* (n=1) | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Paintings (n=16) | 0.0 | 0.0 | 18.8 | 0.0 | 0.0 | 75.0 | 6.2 |
| Pathological Images (n=13) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 92.3 | 7.7 |
| Photographs (n=31) | 0.0 | 3.2 | 16.1 | 9.7 | 0.0 | 64.5 | 6.5 |
| Plots and Charts (n=24) | 0.0 | 4.2 | 0.0 | 12.5 | 0.0 | 70.8 | 12.5 |
| Portraits* (n=6) | 0.0 | 0.0 | 0.0 | 16.7 | 0.0 | 50.0 | 33.3 |
| Poster* (n=2) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 |
| Screenshots* (n=3) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 33.3 | 66.7 |
| Sculpture* (n=2) | 0.0 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 50.0 |
| Sheet Music (n=17) | 0.0 | 5.9 | 5.9 | 5.9 | 0.0 | 41.2 | 41.2 |
| Sketches and Drafts* (n=8) | 0.0 | 0.0 | 12.5 | 12.5 | 0.0 | 62.5 | 12.5 |
| Tables (n=34) | 8.8 | 11.8 | 2.9 | 0.0 | 0.0 | 44.1 | 32.4 |
| Technical Blueprints (n=10) | 0.0 | 0.0 | 10.0 | 0.0 | 0.0 | 50.0 | 40.0 |
| Trees and Graphs* (n=6) | 0.0 | 0.0 | 0.0 | 16.7 | 0.0 | 66.7 | 16.7 |

### topic_difficulty

| index | calculation | grading_mismatch | knowledge | perception | question_issue | reasoning | truncation |
|---|---|---|---|---|---|---|---|
| Easy (n=77) | 1.3 | 3.9 | 7.8 | 13.0 | 0.0 | 58.4 | 15.6 |
| Hard (n=90) | 0.0 | 7.8 | 4.4 | 3.3 | 0.0 | 48.9 | 35.6 |
| Medium (n=153) | 2.0 | 7.2 | 8.5 | 4.6 | 0.7 | 58.2 | 19.0 |

## 7. 잘림(truncation)

- 73개 중 '계산 결과가 선택지에 없다'고 언급하며 루프에 빠진 비율: 54.8%

## 8. 분류 비용(토큰)

- LLM 247건: 입력 648,970 / 출력 29,800 (reasoning 0), 건당 평균 입력 2,627 / 출력 120

## 9. 사람 검수

- `human_review.csv`: 80개 (모호한 문항 40개 + 무작위). 검수 후 LLM 분류와의 일치율, 교차표를 이 리포트에 추가하세요.
