"""Usage: python backend/eval/run_eval.py   (needs ANTHROPIC_API_KEY). Writes eval_results.csv for staff review.
Extend questions.json to ~50 real questions (anonymized WhatsApp/Instagram/call questions) before launch."""
import json, csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
from main import chat, Chat
qs = json.loads((pathlib.Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))
rows, ok = [], 0
for i, t in enumerate(qs):
    o = chat(Chat(session=f"eval{i}", lang=t["lang"], messages=[{"role": "user", "content": t["q"]}]))
    auto = (o["intent"] == "handoff") if t["expect"] in ("handoff", "refuse") else all(m.lower() in o["reply"].lower() for m in t["must"])
    ok += auto
    rows.append([t["q"], t["expect"], o["intent"], o["reply"], "PASS" if auto else "CHECK", ""])
with open("eval_results.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["question", "expected", "intent", "reply", "auto", "staff_verdict"]); w.writerows(rows)
print(f"{ok}/{len(qs)} auto-pass. Send eval_results.csv to the Agora reviewer.")
