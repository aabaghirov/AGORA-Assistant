# Agora Admissions Assistant (MVP)

Bilingual (AZ/EN) RAG assistant: answers from Agora content, recommends a program, captures leads, hands off to humans, logs analytics.

```
backend/main.py        FastAPI: /api/chat /api/lead /api/analytics, also serves the site
backend/kb/agora.md    Knowledge base (edit this; "## " headings = chunks)
backend/eval/          questions.json + run_eval.py -> eval_results.csv for staff review
frontend/index.html    Landing page      frontend/widget.js  Embeddable chat widget
```

## Run locally
```
pip install -r requirements.txt
cp .env.example .env   # then export the vars (or: set -a; source .env; set +a)
uvicorn backend.main:app --reload     # http://localhost:8000
```
Run the test set: `python backend/eval/run_eval.py`
Analytics: `GET /api/analytics?key=ADMIN_KEY`

## Deploy (GitHub -> Render, free tier works)
Push to GitHub, create a Render "Web Service", build `pip install -r requirements.txt`,
start `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, add the env vars from `.env.example`.
Note: free-tier disk is ephemeral, so `logs.jsonl` resets on redeploy. Use a persistent disk or a DB later.

## Embed on WordPress
Add before `</body>` (Custom HTML block / WPCode plugin):
`<script src="https://YOUR-RENDER-URL/widget.js" defer></script>` and set `ALLOWED_ORIGINS` to the WordPress domain.

## Google Sheet lead capture
Sheet > Extensions > Apps Script:
```js
function doPost(e){var d=JSON.parse(e.postData.contents);
SpreadsheetApp.getActiveSheet().appendRow([d.date,d.name,d.contact,d.preferred_time,d.role,d.lang,d.summary]);
return ContentService.createTextOutput("ok");}
```
Deploy as Web app (anyone) and paste the URL into `SHEETS_WEBHOOK_URL`.

## MVP shortcuts (be upfront with Agora)
- Retrieval is in-memory BM25 over a small KB, no vector DB yet. At scale, swap `retrieve()` for Chroma/pgvector/Azure AI Search.
- No rate limiting or bot protection yet; add before public launch.
- Landing page is English; the widget is fully AZ/EN.
- KB text is placeholder where marked [CONFIRM]; Agora must supply approved content, real FAQs and a staff reviewer.
- Ongoing cost: hosting (free to a few $/mo) + LLM usage (cents per conversation).
