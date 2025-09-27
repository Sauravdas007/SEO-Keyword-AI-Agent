# SEO Keyword Research AI Agent (Refactored)

## Overview
This project provides a refactored SEO Keyword Research AI Agent that generates 50 targetable keyword suggestions from a single seed keyword.
It is built as a Flask API so it can be called from automation tools like n8n.

## Files
- agent/: core logic (generate_candidates)
- app.py: Flask API exposing /keywords
- requirements.txt: required packages
- plan.pdf: 1-page development plan
- n8n_workflow.json: sample workflow for auto-import to n8n
- video_script.txt: suggested narration to record with your own voice
- tests/: basic unit tests

## Run locally
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## API usage
GET:
`http://127.0.0.1:5000/keywords?seed=global%20internship&n=50`

POST JSON:
```json
{"seed":"global internship","n":50}
```

## Extending with real SEO APIs
Replace `fetch_metrics_for_keywords` in `agent/generator.py` by providing a `fetcher` argument to `generate_candidates`
that calls SerpAPI / Ahrefs / Google Ads to fetch volumes and competition scores.

## n8n integration
Import `n8n_workflow.json` in your n8n instance and update the HTTP Request URL to point to your deployed Flask server.
