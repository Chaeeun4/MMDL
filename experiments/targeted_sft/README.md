# MMMU 약점 보강 SFT 실험 계획

**목표는 MMMU와 MMMU-Pro 전체 점수를 올리는 것이다.** 오답을 보니 모델은 그림에서 선이 어디로 이어지는지 잘못 읽거나, 읽은 숫자 중 필요한 것을 계산에서 빼기도 했다. 세 모델을 같은 원본 모델에서 출발시킨다. 하나는 일반 시각 추론 데이터(ViRL39K)로만 학습하고, 나머지 둘은 일부를 연결 그림 문제나 표 계산 문제로 바꿔 학습한다. 각 능력이 좋아졌는지와 전체 점수가 올랐는지를 따로 본다. SFT는 이미지·질문·예시 답변으로 모델을 추가 학습하는 방법이다.

## 지금 진행할 순서

1. **GPU 평가 완료 확인.** 기존 큐에서 PrIMuS seed 42가 `seeds` 모드로 돌고 있다면 60문항 단계다. `full`은 Base와 PrIMuS step 500의 900문항·32K·`legacy_cot`·seed 3407 비교다. 완료된 경우 재실행할 필요가 없다.
2. **공개 데이터 예시 확인.** GPU 평가가 도는 동안 AI2D·ECD에서 각각 20~30개를 뽑는다. 이미지가 열리는지, 정답을 확인할 수 있는지, 선을 따라가거나 조건에 맞춰 계산해야 답할 수 있는 문제인지 살펴본다. 공개 ViRL39K는 검토할 수 있고, 진아님의 실제 C1b 선별 풀이를 재사용하려면 JSONL·이미지 경로·제외 기록이 필요하다.
3. **동일 조건의 900문항 결과 분석.** 두 실행의 문항 ID와 정답을 맞춘 뒤 전체 900, Music·Chemistry 60, 나머지 840의 맞힌 문제 수와 정답↔오답으로 바뀐 문항을 비교한다.
4. **중복을 확인한 뒤 학습.** 그림의 연결을 읽는 문제와 표의 조건·단위를 써서 계산하는 문제를 고른다. 일반 데이터만 쓴 모델과 각 문제 유형을 섞은 모델의 학습량을 맞춘다.

900문항 원본 결과는 `runs/controlled_legacy_cot/900q/context-32768/seed-3407/{base,primus_only}/`의 `metrics.json`과 `predictions.jsonl`이다. 현재 체크아웃에서는 두 실행의 새 결과를 확인하지 못했다. `full`이 누락됐고 기존 작업이 끝났다면 GPU 서버에서 [평가 큐](../../scripts/queue_mmmu_controlled.sh)의 `full` 모드를 실행한다.

## 기존 점수와 해석

| MMMU validation 900문항 실행 | 정답 및 정확도 | 비교 조건 |
|---|---:|---|
| Base 1005 재채점 | 583/900 · 64.78% | 16K에서 생성한 출력 재채점 |
| PrIMuS step 500 rerun | 575/900 · 63.89% | 32K·기본 픽셀 범위 |
| PrIMuS 저장본 | 569/900 · 63.22% | 1,310,720~5,242,880 pixels |
| PubChem 저장본 | 555/900 · 61.67% | 같은 픽셀 범위, 재채점 시 558/900 |
| Jina `official` | Base 550, CM 550, C2CM 537 | 같은 프롬프트 안에서 비교 |
| Jina `describe_cot` | Base 569, C1 572, CM 573 | 같은 프롬프트 안에서 비교 |

60문항 `legacy_cot`에서는 Base 24→PrIMuS 29였고, 900문항 PrIMuS rerun의 동일 60문항은 22였다. 기존 16K Base와 32K PrIMuS의 전체 점수 차이에는 평가 조건 차이가 포함돼 있다. 이번 첫 실험에서는 일반 문제의 25%를 특정 유형으로 교체했을 때 어떤 차이가 생기는지 본다. [900문항 전체 집계와 입력 위치](../../reports/sft_analysis/mmmu_900_error_types.md) · [Music·Chemistry 문항 비교](../../reports/sft_analysis/mmmu_error_analysis.md)

C1·CM·C2CM은 모두 원본 Qwen3-VL-4B-Instruct에서 별도로 LoRA SFT를 시작했다. C1은 ViRL 풀이를 짧은 순서로 선별했다. CM은 C1의 생성 결과를 다시 선별한 C1b를 replay로 사용했다. C2CM은 같은 생성 결과와 Claude 풀이를 합쳐 다시 선별했다. CM과 C2CM 사이에는 교사 풀이 외에도 replay 양과 업데이트 수 차이가 있다.

## 무엇을 비교하고 어떻게 판단할까?

이 문서에서 **일반 SFT 모델**은 원본 Qwen3-VL-4B-Instruct를 ViRL39K의 일반 시각 추론 문제로만 추가 학습한 대조군이다. **연결 보강 모델**은 그 학습 문제 일부를 AI2D 연결 문제로 바꾸고, **표 계산 보강 모델**은 일부를 ECD 조건·계산 문제로 바꾼다.

| 확인할 질문 | 두 모델에 주는 문제 | 판단 기준 |
|---|---|---|
| **H1. 연결 보강 모델이 선을 더 잘 따라가는가?** | 학습에 넣지 않은 자체 제작 그림 두 장. 두 그림의 배치는 같고, 밸브 V에서 나온 선만 첫 그림에서는 탱크 A, 둘째 그림에서는 탱크 B로 이어진다. 두 그림에 같은 질문을 한다. | 한 모델이 첫 그림에 A, 둘째 그림에 B를 답해야 그 한 쌍을 맞힌 것으로 센다. 연결 보강 모델이 일반 SFT 모델보다 더 많은 쌍을 맞혔는지 본다. |
| **H2. 표 계산 보강 모델이 필요한 값을 찾아 단위를 맞추고 계산하는가?** | 같은 표 문제를 두 번 푼다. 한 번은 표를 **이미지**로 주고, 한 번은 표의 **모든 값과 단위를 확인한 텍스트**로 준다. 질문은 두 번 모두 같다. | 이미지 조건과 텍스트 조건에서 각각 **질문에 맞는 행·열 선택**, **단위 변환**, **최종 답**을 따로 채점한다. 항목별로 표 계산 보강 모델이 일반 SFT 모델보다 더 많이 맞혔는지 본다. |
| **H3. 전체 점수도 좋아지는가?** | 최종 후보, 학습 전 Base, 일반 SFT 모델을 각각 같은 MMMU test와 MMMU-Pro test에서 평가한다. | 벤치마크별 전체 정확도 차이를 보고한다. H1·H2의 문제를 더 잘 풀어도 전체 점수는 별개로 확인한다. |

**H1의 질문 예시**는 “밸브 V에서 나온 물은 어느 탱크로 가나요?”다. 우리 팀이 새로 만든 도식 한 쌍을 통째로 검증에 둔다. MMMU나 MMMU-Pro의 그림은 이 짝을 만드는 데 사용하지 않는다.

**H2의 질문 예시**는 “A 구간에서 물이 얼마나 줄었나요?”다. 팀이 만든 표에서 A는 시작 1.2 L·끝 850 mL, B는 시작 700 mL·끝 0.9 L로 적는다. 모델에게 표 이미지 또는 이 표 전체를 옮긴 텍스트와 질문을 준다. 채점할 때 **A행의 시작·끝 값 선택**, **1.2 L를 1,200 mL로 변환**, **최종 답 350 mL**를 따로 확인한다. 계산 과정과 답은 모델 입력에서 뺀다.

보강 전에는 이미지에서 모델이 직접 읽어낸 표도 같은 텍스트 형식으로 넣어 비교한다. 확인된 표를 주면 맞히는 사례는 그림에서 값을 읽는 단계부터 본다. 확인된 표에서도 A 대신 B를 고르거나 계산이 틀리면, 조건에 맞는 값을 골라 쓰는 단계를 본다. [대표 9문항의 원본 이미지와 풀이](../../reports/sft_analysis/mmmu_general_failure_review.html) · [Music·Chemistry 검토 HTML](../../reports/sft_analysis/mmmu_manual_review.html)

## 데이터 다운로드

| 용도 | 데이터와 다운로드 | 첫 선별 기준 |
|---|---|---|
| 연결 관계 | [AI2D 원본 ZIP](https://ai2-public-datasets.s3.amazonaws.com/diagrams/ai2d-all.zip) · [공식 배포 안내](https://registry.opendata.aws/allenai-diagrams/) · [AI2D-RST 연결 주석](https://github.com/thiippal/AI2D-RST) | AI2D 공식 train 이미지에서 화살표 방향, 연결 대상, 경로를 읽어야 답할 수 있는 문항을 고른다. RST 주석은 원본 이미지 ID로 연결한다. |
| 조건·값·단위 적용 | [ECD 학습 데이터](https://huggingface.co/datasets/ChartFoundation/ECD-10k-Images) · [저자 다운로드 및 전처리 안내](https://github.com/yuweiyang-anu/ECD/blob/main/datasets/README.md) | 해당 계열이나 조건을 선택한 뒤 차이·비율을 계산하는 문항을 고른다. 단위 변환이 실제로 필요한 문항을 따로 표시하고, 원천값으로 확인 가능한 답부터 사용한다. |
| 일반 시각 추론 | [ViRL39K 공개 원본](https://huggingface.co/datasets/TIGER-Lab/ViRL39K) | 공개 원본은 바로 검토할 수 있다. 진아님의 C1b를 재현하려면 선별된 풀이 JSONL, 실제 이미지 경로, 제외 ID 또는 중복 검사 기록을 별도로 확보한다. |

ECD는 Hugging Face 데이터 뷰어에서 JSON 스키마 오류가 표시돼 저자 저장소의 파일별 다운로드 안내를 우선 사용한다. [ECDBench](https://huggingface.co/datasets/ChartFoundation/ECDBench)는 저자들이 별도로 배포한 평가셋이므로 학습 후보에서 제외한다.

## H1. 연결 관계를 읽는 능력

전자공학 30번에서 모델은 부품 이름과 수치를 읽었지만, 접지로 내려가는 저항을 직렬 경로에 넣었다. 기호 인식과 연결 관계 판독을 따로 측정할 근거다. [오답 사례](../../reports/sft_analysis/mmmu_general_failure_review.html#E30)

- **데이터 근거.** AI2D는 과학 도식과 구성 요소·관계 주석, 질의응답을 제공한다. AI2D-RST는 일부 원본 도식의 연결 관계를 그래프로 주석화했다. [Kembhavi 등, ECCV 2016](https://ai2-website.s3.amazonaws.com/publications/Diagrams_ECCV2016.pdf) · [Hiippala 등, AI2D-RST](https://doi.org/10.1007/s10579-020-09517-1)
- **실험 근거.** Hou 등은 요소 인식과 관계 추론을 분리해 평가했다. 관계선을 제거하거나 바꿔도 모델이 기존 답을 유지한 사례를 보여, 답이 그림 속 연결을 따라가는지 직접 검사할 이유를 제시했다. [Hou 등, ICML 2025](https://proceedings.mlr.press/v267/hou25c.html)
- **우리 실험.** AI2D train에서 연결 QA를 선별한다. 검증에는 위의 밸브 예시처럼 연결 하나만 다른 새 그림 두 장을 사용한다. 두 그림을 모두 맞힌 쌍의 비율과, 그림 속 기호를 맞힌 비율을 따로 기록한다.

## H2. 읽은 값을 조건·단위에 맞게 쓰는 능력

전자공학 5번에서 모델은 그림 속 값을 일부 읽었지만 출력 저항 계산에 필요한 항을 누락했다. 건축·공학 23번에서는 높이 변화가 없다는 표의 주석을 방향 조건으로 해석했다. [전자공학 사례](../../reports/sft_analysis/mmmu_general_failure_review.html#E5) · [건축·공학 사례](../../reports/sft_analysis/mmmu_general_failure_review.html#A23)

- **데이터 근거.** ECD는 다양한 합성 차트와 QA로 튜닝하고 여러 차트 평가에서 성능 개선을 보고했다. 이번 실험에서는 단순 제목·값 읽기 문항과 조건 선택·단위 적용·계산 문항을 분리해 선별한다. [Yang 등, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Yang_Effective_Training_Data_Synthesis_for_Improving_MLLM_Chart_Understanding_ICCV_2025_paper.html)
- **실험 근거.** ChartQA에서 VisionTaPas의 test 정확도는 추출 표를 썼을 때 45.52%, 검증된 원본 표를 제공했을 때 61.84%였다. 원천값을 제공하는 대조 조건은 값 추출과 이후 추론의 차이를 조사하는 데 쓸 수 있다. [Masry 등, ChartQA Table 5](https://aclanthology.org/2022.findings-acl.177.pdf)
- **우리 실험.** 위의 물 사용량 예시처럼 같은 질문을 표 이미지, 모델이 읽은 표, 확인된 표로 각각 푼다. 두 텍스트 표는 같은 형식으로 적고 최종 답과 계산식은 주지 않는다.

## 일반 데이터 혼합과 전체 성능

순차 멀티모달 학습에서 이전 과제 샘플을 다시 섞는 replay가 망각을 완화한 연구가 있다. ViRL39K는 여러 출처의 검증 가능한 시각 추론 데이터로, 일반 훈련 후보를 고르는 근거가 된다. 이번 설계에서는 모든 실험이 원본 Base에서 시작하므로 **일반 데이터 혼합 SFT**로 기술한다. 먼저 전체 학습 문제의 4분의 1을 바꿔 본다. 효과를 본 뒤 비율을 조정할 수 있다. [Continual Instruction Tuning for Large Multimodal Models, §5.3](https://arxiv.org/html/2311.16206#S5.SS3) · [VL-Rethinker](https://arxiv.org/abs/2504.08837)

| 조건 | 학습 구성 |
|---|---|
| 대조군 | 일반 ViRL 100% |
| 관계 보강 | 공통 ViRL 75% + AI2D 관계 QA 25% |
| 조건 보강 | 공통 ViRL 75% + ECD 조건·계산 QA 25% |

세 조건의 시작 모델, LoRA 대상, 업데이트 수, 평가 설정을 고정하고 실제 학습 토큰 수를 기록한다. 자체 검증에서 해당 능력을 측정하고 MMMU validation 900문항에서 전체 정확도를 비교한다. 후보를 확정한 뒤 MMMU test와 MMMU-Pro test에서 원본 Base 및 일반 ViRL 대조군 대비 전체 정확도를 보고한다. MMMU-Pro의 Standard와 Vision 결과는 따로 기록한다.

## 다음 작업과 중복 검사

1. AI2D와 ECD에서 각각 20~30문항을 먼저 확보한다. 이미지가 열리는지, 정답을 확인할 수 있는지, 실제로 목표 능력이 필요한지 확인한다.
2. 최종 후보의 데이터셋 리비전, split, 샘플 ID, 이미지 출처, 동일 이미지 그룹을 기록한다. 같은 이미지에서 나온 질문은 모두 학습에 넣거나 모두 검증에 넣는다. 한 이미지의 질문을 양쪽에 나누어 넣지 않는다.
3. 후보를 MMMU dev·validation·test와 MMMU-Pro Standard·Vision에 대조한다. 정규화 텍스트와 8-gram, 이미지 해시와 근접 유사도, Vision 이미지의 OCR을 검사한다. 동일 평가 이미지의 크롭·리사이즈본도 제외하고 검사 범위와 제외 이유를 기록한다. [MMMU 공식 데이터](https://huggingface.co/datasets/MMMU/MMMU) · [MMMU-Pro 공식 데이터](https://huggingface.co/datasets/MMMU/MMMU_Pro)

### 왜 문제 문장과 이미지를 따로 검사하나?

연구에서도 두 신호를 따로 본다. 평가 그림에 다른 질문을 붙여도 그림은 겹칠 수 있고, 반대로 “어떤 항목이 가장 큰가?”처럼 흔한 질문은 다른 그림에도 많이 나온다. 이 프로젝트에서는 **둘 중 하나라도 후보로 잡히면 확인**하고, 실제 중복이 확인된 샘플을 학습에서 뺀다.

| 검사 | 연구에서 사용한 방법 | 우리 데이터에 적용하는 방법 |
|---|---|---|
| **문제 문장 검사** | LMMs-Eval은 LLaVA 학습 자료와 평가셋의 텍스트를 비교할 때 8-gram을 썼다. 그림은 별도의 이미지 토큰 방식(SEED)으로 비교했다. 두 방법을 함께 사용해 동일 이미지, 유사 이미지, 유사 문항 사례를 찾았다. [Zhang 등, LMMs-Eval §4.1](https://arxiv.org/html/2407.12772#S4.SS1) | 문제와 선택지를 정규화해 완전 일치 및 연속 8단어 겹침을 찾는다. MMMU-Pro Vision은 화면에 들어간 문제를 OCR로도 읽는다. 흔한 문제 틀은 후보로만 두고, 구체적 문장·값·선택지를 대조한다. 8-gram은 짧은 질문이나 번역·바꿔쓰기를 놓칠 수 있다. [Rethinking Benchmark and Contamination for Language Models with Rephrased Samples](https://arxiv.org/abs/2311.04850) |
| **그림 해시 검사** | Apertus 1.5는 학습 이미지의 지각 해시를 평가 이미지 약 95만 장과 대조했다. 위성·의학처럼 서로 다른 이미지도 비슷하게 보이는 분야에서는 오탐이 생긴다고 보고했다. [Apertus 1.5 기술보고서 §4.2](https://arxiv.org/html/2610.15542#S4.SS2) | 파일 해시로 동일 파일을 찾고, 지각 해시로 저장 방식이나 크기가 달라진 그림의 후보를 찾는다. 도식·표에서 해시가 가깝다면 두 그림을 열어 재사용인지 확인한다. |
| **SigLIP 이미지 검색** | SEA-VL은 중복 이미지 후보 탐색에서 지각 해시, CLIP-ViT, Nomic Embed Vision과 SigLIP을 직접 비교했다. 사람이 검토한 상위 후보에서 SigLIP의 정밀도가 59.33%였고, 전체 수집 자료를 처리할 때는 속도를 고려해 Nomic을 사용했다. [Cahyawijaya 등, SEA-VL §5.2, Table 2](https://aclanthology.org/2025.acl-long.916.pdf#page=7) | SigLIP은 이미지를 벡터로 바꾸고, 평가 이미지 중 비슷한 그림을 검색하는 데 쓴다. 유사도는 검토 대상을 찾는 신호다. 같은 양식의 표라도 숫자나 연결선이 다를 수 있어, 유사도만으로 삭제하지 않는다. |

**우리 기준의 근거와 한계.** 문장과 이미지를 따로 보는 데는 위 연구 사례가 있다. 다만 SEA-VL의 수치는 그 연구의 상위 후보 검토 결과다. MMMU·MMMU-Pro의 회로·표에 그대로 적용되는 임계값이나 재현율은 제공하지 않는다. 우리 자료에서 동일 그림의 크롭·리사이즈와, 비슷한 양식에 내용만 다른 그림을 예시로 점검한 뒤 검색 기준을 정한다. 후보에는 평가 문항 ID, 학습 샘플 ID, 어떤 검사에서 잡혔는지, 유지·제외 이유를 남긴다. 이 검사의 대상은 이번에 추가할 SFT 데이터다.

## 로컬 데이터 준비

로컬 데이터 루트는 `~/datasets/targeted_sft/`다. 원본 파일은 `raw/{ai2d,ecd,virl}/`에 두고, 변환한 파일과 복사할 이미지는 `prepared/`에 둔다.

| 자료 | 현재 상태 |
|---|---|
| AI2D | 로컬 ZIP에서 연결 관련 질문을 키워드로 골라 이미지가 서로 다른 25문항을 추출했다. 공식 train/test 구분과 MMMU·MMMU-Pro 중복은 아직 검사하지 않았다. |
| ECD | 다운로드된 원본에서 서로 다른 이미지의 계산·비교 후보 25문항을 뽑았다. ShareGPT 형식, 이미지 경로 및 이미지 디코딩을 확인했다. |
| ViRL39K | Parquet 38,870행을 읽었다. 이미지 참조 37,812개가 모두 ZIP에 있었고, 그중 25개를 실제로 열었다. |
| MMMU-Pro | 로컬 캐시에서 Standard 4지선다·10지선다와 Vision을 각각 1,730행씩 읽을 수 있다. |
| MMMU | 로컬 캐시에 기존 평가 코드가 지정한 리비전 `98e6ac0cb9b7b2cd2c991b85a50762edc4aedc68`이 있다. |
| `cm_derived` | 화학·음악 train/val JSONL 8개가 있다. C1b replay나 이미지 파일이 없고, JSONL의 이미지 경로는 현 머신에 존재하지 않는다. |

AI2D와 ECD의 결과는 `prepared/{ai2d,ecd}_pilot_sharegpt.json`과 `prepared/{ai2d,ecd}_pilot_review.csv`다. 원본을 다시 준비할 때는 MMDL 저장소 루트에서 아래 명령을 실행한다. [파일럿 변환 코드](prepare_pilot.py)

```bash
hf download ChartFoundation/ECD-10k-Images ECD_QAs_All.json images.tar codes.tar meta_information_all.json --repo-type dataset --local-dir ~/datasets/targeted_sft/raw/ecd
hf download TIGER-Lab/ViRL39K 39Krelease.parquet images.zip --repo-type dataset --local-dir ~/datasets/targeted_sft/raw/virl
python3 experiments/targeted_sft/prepare_pilot.py ecd
```

중복 검사에서는 ViRL의 `images.zip`과 ECD의 `images.tar`에서 이미지를 직접 읽을 수 있다. 실제 학습 파일에서 참조할 이미지 파일만 `prepared/images/`에 풀면 된다. AI2D·ECD 파일럿 이미지 25장씩은 이미 해당 폴더에 있다.

원본 MMMU는 [평가 코드](../../code/dataset.py)의 리비전과 맞춘다. 인터넷에 연결된 터미널에서 아래 명령을 쓰면 된다.

```bash
hf download MMMU/MMMU --repo-type dataset --revision 98e6ac0cb9b7b2cd2c991b85a50762edc4aedc68
```

ShareGPT 파일의 이미지 경로는 `targeted_sft/prepared/images/...`다. 원격의 `/shared_dir/LLaMA-FACTORY/dataset/targeted_sft/`에 복사한 뒤, LLaMA-Factory의 `dataset_dir`과 `media_dir`은 그 상위인 `/shared_dir/LLaMA-FACTORY/dataset`을 사용한다. 등록할 때 ShareGPT의 `messages`는 `conversations`, `images`는 `images` 열에 연결한다. [LLaMA-Factory ShareGPT 멀티모달 명세](https://github.com/hiyouga/LlamaFactory/blob/main/data/README.md#multimodal-image-dataset)

파일럿 CSV에 검수·중복 검사 상태를 기록한다. 학습 후보로 승인된 행만 최종 학습 파일에 넣는다. 전량 중복 검사와 새 SFT는 아직 수행하지 않았다.

## 중복 검사 실행

[검사 코드](check_overlap.py)는 파일럿 CSV 또는 같은 형식의 최종 후보 CSV를 받아 원본 ZIP·TAR에서 이미지를 읽는다. `source`, `sample_id`, `group_id`, `question`이 필수이고 `choices`는 선택이다. ViRL은 `source=virl`과 원본 Parquet의 `qid`를 `sample_id`에 사용한다. AI2D·ECD는 파일럿 CSV처럼 `group_id`에 출처와 원본 이미지 ID를 적는다.

```bash
cd ~/MMDL
.venv/bin/python experiments/targeted_sft/check_overlap.py \
  --manifest ~/datasets/targeted_sft/prepared/{ai2d,ecd}_pilot_review.csv \
  --out ~/datasets/targeted_sft/prepared/overlap_pilot
```

다시 실행할 때는 새 출력 폴더를 지정한다. 검사기는 MMMU 30과목과 세 split, MMMU-Pro Standard 4·10 및 Vision의 행 수를 확인한다. 결과 폴더에 `matches.csv`(어떤 평가 항목과 어떻게 걸렸는지), `candidates.csv`(후보별 검토 상태), `summary.json`(리비전·검사 범위·설정)이 생긴다.

기본 검사는 정규화 텍스트, 8-gram, 원본 파일과 디코딩 픽셀의 SHA-256, pHash를 사용한다. `--vision-ocr`은 Pro Vision 화면의 글자를 읽는 검사만 추가한다. `--siglip-model`은 이미지 임베딩 검색을 추가한다. 다음 전수 검사 명령은 두 항목을 모두 요구한다.

### 원본 학습 데이터 전수 검사

`--all-raw`는 후보 CSV를 만들지 않고 학습 데이터 원본에서 모든 질문을 읽는다. 현재 로컬 원본은 AI2D 15,501문항, ECD 321,544문항, ViRL39K 38,870문항으로 총 375,915문항이다. ECD는 설명형과 추론형을 모두 포함한다.

```bash
cd /home/cepark/MMDL
.venv-overlap/bin/python experiments/targeted_sft/check_overlap.py --all-raw \
  --siglip-model google/siglip-base-patch16-224 \
  --out ~/datasets/targeted_sft/prepared/overlap_all_raw
```

이 모드는 텍스트·해시·Vision OCR·SigLIP 검사를 모두 실행한다. 입력에는 `--manifest`를 쓰지 않는다. 파일럿 또는 선별 후보만 비교할 때는 `--all-raw` 대신 `--full --manifest <기존 CSV 경로>`를 쓴다. 출력 폴더는 완료 후에만 만들어지며, 이미 같은 이름의 폴더가 있을 때는 새 경로를 지정한다.


### GPU 평가가 끝난 뒤 자동으로 시작

기존 평가 큐가 쓰는 `runs/controlled_legacy_cot/.queue.lock`을 기다리는 [실행 스크립트](run_overlap_after_eval.sh)를 사용한다. 큐가 잠금을 풀고 Base와 PrIMuS의 900문항 출력이 모두 있으면 CUDA에서 검사를 시작한다. 평가가 실패해 출력이 빠졌으면 검사도 중단한다. 검사 시작·완료·오류를 기존 평가 큐와 같은 Discord 웹훅으로 알린다. 오류 알림에는 실패 단계, 종료 코드, 로그 끝부분을 담는다. 웹훅을 교체할 때는 `DISCORD_WEBHOOK_URL`이나 `DISCORD_WEBHOOK_FILE`로 지정할 수 있다.

GPU 서버에 코드, 학습 원본 압축과 문항 파일, 평가 캐시, SigLIP 가중치, Tesseract 영어 데이터를 준비한 뒤 실행한다. `--root`와 `--hub-cache`에는 GPU 서버의 실제 경로를 지정한다. `.venv-overlap` 위치가 다르면 `OVERLAP_PYTHON`에 해당 Python 절대경로를 지정한다.

```bash
cd /shared_dir/MMDL
nohup bash experiments/targeted_sft/run_overlap_after_eval.sh \
  --root /shared_dir/LLaMA-FACTORY/dataset/targeted_sft \
  --hub-cache /shared_dir/huggingface_cache/hub \
  --siglip-model google/siglip-base-patch16-224 \
  --out /shared_dir/LLaMA-FACTORY/dataset/targeted_sft/prepared/overlap_all_raw \
  > overlap_queue.log 2>&1 < /dev/null &
```

전수 검사는 평가용 `.venv`와 분리된 `.venv-overlap`에서 실행한다. 이 환경에서 Transformers 5.17.0과 huggingface-hub 1.33.0 로딩, 캐시된 SigLIP 모델의 이미지 검색, Tesseract 영어 OCR을 각각 작은 입력으로 확인했다. SigLIP의 PIL 기반 이미지 처리기를 사용하므로 Torchvision은 필요하지 않다. 모델은 검사 시 로컬 캐시에서 읽는다.

- 모든 후보 이미지를 모든 고유 평가 이미지와 비교한다. `--siglip-device auto`는 CUDA가 있으면 사용하며, 메모리가 부족하면 `--siglip-batch-size`를 낮춘다. `--siglip-threshold` 기본값 0.92는 후보 검색의 시작점이며, 이 데이터에 대해 검증된 기준은 아니다.
- 평가 파일, 학습 후보 이미지, 모델, OCR 도구가 빠지거나 Vision OCR이 빈 결과를 반환하면 오류로 멈춘다. 성공한 결과의 `summary.json`에는 출처별 문항 수, 확인한 이미지 참조 수, 평가 리비전·범위, OCR 및 SigLIP 설정이 적힌다.
- `no_match_found`는 적용한 방법에서 후보를 찾지 못했다는 뜻이다. `review_needed`는 그림과 질문을 확인해서 유지하거나 제외한다. 동일 차트의 여러 질문에서 이미지 비교 결과를 재사용한다. 검사기는 이미지를 풀거나 학습 데이터를 삭제하지 않는다.

파일럿 실행에서는 AI2D 25문항·ECD 25문항을 MMMU 11,550행과 MMMU-Pro 5,190행(Standard 4·10 및 Vision의 합계)에 대조했다. 기본 검사에서 중복 후보는 0건이었고 Vision OCR과 SigLIP은 실행하지 않았다. 결과는 `~/datasets/targeted_sft/prepared/overlap_pilot/`에 있다.
