import os, json, re, time, math, smtplib, pathlib, collections
from email.message import EmailMessage
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from anthropic import Anthropic

ROOT = pathlib.Path(__file__).parent
MODEL = os.getenv("MODEL", "claude-sonnet-5-5")
LOG = ROOT / "logs.jsonl"
client = Anthropic()
app = FastAPI(title="Agora Admissions Assistant")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])

# ---------- Knowledge base: chunk on "## ", BM25 retrieval ----------
# Tokens are cut to 5 chars so Azerbaijani suffixes (universitetlər/universitetə) still match.
def tok(s): return [w[:5] for w in re.findall(r"\w+", s.lower())]
CHUNKS = [p.strip() for f in sorted((ROOT / "kb").glob("*.md"))
          for p in re.split(r"\n(?=## )", f.read_text(encoding="utf-8")) if p.strip()]
DOCS = [tok(c) for c in CHUNKS]; N = len(DOCS); AVG = sum(map(len, DOCS)) / max(N, 1)
DF = collections.Counter(t for d in DOCS for t in set(d))

def retrieve(q, k=4):
    qt, sc = tok(q), []
    for i, d in enumerate(DOCS):
        tf, s = collections.Counter(d), 0
        for t in qt:
            if t in tf:
                s += math.log(1 + (N - DF[t] + .5) / (DF[t] + .5)) * tf[t] * 2.2 / (tf[t] + 1.2 * (.25 + .75 * len(d) / AVG))
        sc.append((s, i))
    return [CHUNKS[i] for s, i in sorted(sc, reverse=True)[:k] if s > 0]

SYSTEM = """You are the Admissions Assistant for Agora, an education consultancy in Baku helping students apply abroad.
RULES
- Answer ONLY from CONTEXT. If the answer is not there, say you are not sure and offer a human consultant. Never guess.
- Never promise admission or scholarships. Never state prices, fees or deadlines unless they appear in CONTEXT.
- Reply in the user's language (Azerbaijani or English). Max ~110 words, friendly, plain.
- To recommend a program, ask ONE question at a time: current grade/year, target countries, intended major, timeline. Then recommend START, FORWARD or RISE with a one-line reason and offer to book a free initial consultation.
- If the user wants to book or talk to someone, set intent "book".
Return ONLY JSON: {"reply": "...", "intent": "faq|recommend|book|handoff|other", "answered": true|false}"""

HANDOFF = re.compile(r"price|cost|fee|how much|pay|guarantee|refund|complain|scam|angry|"
                     r"qiym[əe]t|haqq|neçə pul|ödən|z[əe]man[əe]t|şikay[əe]t|pul", re.I)
T = {"en": "That's best answered by a consultant who can look at your situation. I can pass your details to the team, they usually reply quickly.",
     "az": "Bu sualı vəziyyətinizə baxa bilən məsləhətçimiz cavablandırsa daha dəqiq olar. Məlumatlarınızı komandaya ötürə bilərəm."}

def log(ev, **kw):
    with LOG.open("a", encoding="utf-8") as f: f.write(json.dumps({"t": time.time(), "ev": ev, **kw}, ensure_ascii=False) + "\n")

class Chat(BaseModel):
    session: str; lang: str = "en"; messages: list[dict]

@app.post("/api/chat")
def chat(c: Chat):
    last = c.messages[-1]["content"]
    if HANDOFF.search(last):
        out = {"reply": T.get(c.lang, T["en"]), "intent": "handoff", "answered": False}
    else:
        q = " ".join(m["content"] for m in c.messages[-3:] if m["role"] == "user")
        ctx = "\n\n".join(retrieve(q) or CHUNKS)
        r = client.messages.create(model=MODEL, max_tokens=500, messages=c.messages[-10:],
                                   system=f"{SYSTEM}\nUI language: {c.lang}\nCONTEXT:\n{ctx}")
        txt = r.content[0].text
        try: out = json.loads(re.search(r"\{.*\}", txt, re.S).group())
        except Exception: out = {"reply": txt, "intent": "other", "answered": True}
    if out.get("answered") is False and out.get("intent") not in ("handoff", "book"): out["intent"] = "handoff"
    log("chat", session=c.session, q=last, intent=out.get("intent"), answered=out.get("answered"), lang=c.lang)
    return out

# ---------- Lead capture: Google Sheet webhook + email ----------
class Lead(BaseModel):
    session: str; name: str; contact: str; time: str = ""; role: str = "student"
    lang: str = "en"; consent: bool; transcript: list[dict] = []

@app.post("/api/lead")
def lead(l: Lead):
    if not l.consent: raise HTTPException(400, "Consent required")
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in l.transcript[-12:])
    try:
        summary = client.messages.create(model=MODEL, max_tokens=200, messages=[{"role": "user",
            "content": f"Summarize this admissions chat for a staff member in 3 short lines (interests, grade, countries, open questions):\n{convo}"}]).content[0].text
    except Exception: summary = convo[-600:]
    row = {"date": time.strftime("%Y-%m-%d %H:%M"), "name": l.name, "contact": l.contact, "preferred_time": l.time,
           "role": l.role, "lang": l.lang, "summary": summary}
    if u := os.getenv("SHEETS_WEBHOOK_URL"):
        try: httpx.post(u, json=row, timeout=10, follow_redirects=True)
        except Exception as e: log("error", where="sheets", msg=str(e))
    if (h := os.getenv("SMTP_HOST")) and os.getenv("LEAD_EMAIL_TO"):
        try:
            m = EmailMessage(); m["Subject"] = f"New consultation request: {l.name}"
            m["From"] = os.getenv("SMTP_USER"); m["To"] = os.getenv("LEAD_EMAIL_TO")
            m.set_content("\n".join(f"{k}: {v}" for k, v in row.items()))
            with smtplib.SMTP(h, 587) as s: s.starttls(); s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")); s.send_message(m)
        except Exception as e: log("error", where="email", msg=str(e))
    log("lead", session=l.session, lang=l.lang)
    return {"ok": True}

# ---------- Analytics ----------
@app.get("/api/analytics")
def analytics(key: str = ""):
    if key != os.getenv("ADMIN_KEY", "change-me"): raise HTTPException(401)
    ev = [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines()] if LOG.exists() else []
    chats = [e for e in ev if e["ev"] == "chat"]
    sess, leads = {e["session"] for e in chats}, {e["session"] for e in ev if e["ev"] == "lead"}
    return {"sessions": len(sess), "messages": len(chats), "leads": len(leads),
            "conversion_pct": round(100 * len(leads) / max(len(sess), 1), 1),
            "handoffs": sum(e["intent"] == "handoff" for e in chats),
            "unanswered": [e["q"] for e in chats if e["answered"] is False][-20:],
            "top_questions": collections.Counter(e["q"].lower()[:80] for e in chats).most_common(10),
            "by_language": dict(collections.Counter(e["lang"] for e in chats)),
            "dropoff_sessions": len(sess - leads)}

app.mount("/", StaticFiles(directory=ROOT.parent / "frontend", html=True), name="site")
