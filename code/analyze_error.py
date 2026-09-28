import json
from collections import defaultdict

file_path = "results/opt_predictions.jsonl"

total_wrong = 0
format_mismatch_suspects = 00
subject_wrongs = defaultdict(int)

print("="*60)
print("🔍 [MMMU 오답 원인 정밀 분석 리포트]")
print("="*60)

wrong_samples = []

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        if not data.get("correct", False):
            total_wrong += 1
            sub = data.get("subject", "Unknown")
            subject_wrongs[sub] += 1
            
            raw = data.get("prediction_raw", "")
            gold = data.get("gold", "")
            pred = data.get("prediction", "")
            
            # 파서가 Final Answer나 boxed를 못 찾고 끝단 알파벳을 긁어왔는지 체크
            has_final_keyword = "Final Answer" in raw or "box" in raw or "Answer:" in raw
            if not has_final_keyword:
                format_mismatch_suspects += 1
                
            # 오답 샘플 수집 (예시 출력을 위해 몇 개 저장)
            if len(wrong_samples) < 3:
                wrong_samples.append({
                    "id": data.get("id"),
                    "subject": sub,
                    "gold": gold,
                    "pred": pred,
                    "raw_snippet": raw[:300].replace("\n", " ")
                })

print(f"총 오답 문항 수 : {total_wrong}개")
print(f"포맷 지시 위반 / 키워드 누락 의심 (파서 한계 추정) : {format_mismatch_suspects}개")
print(f"논리 전개 후 정답 도출 실패 (모델 실력 한계 추정) : {total_wrong - format_mismatch_suspects}개")

print("\n📉 [과목별 오답 분포 Top 5]")
sorted_wrongs = sorted(subject_wrongs.items(), key=lambda x: x[1], reverse=True)
for sub, cnt in sorted_wrongs[:5]:
    print(f"- {sub}: {cnt}개 오답")

print("\n📝 [대표적 오답 샘플 미리보기 (최대 3개)]")
for i, sample in enumerate(wrong_samples, 1):
    print(f"\n[{i}] ID: {sample['id']} ({sample['subject']})")
    print(f"    - 정답(Gold): {sample['gold']} | 모델 예측(Pred): {sample['pred']}")
    print(f"    - 모델 답변 요약: {sample['raw_snippet']}...")

print("="*60)