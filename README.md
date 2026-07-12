# TnufaReview

An AI copilot for the Israel Innovation Authority **"Tnufa"** grant application. Upload the filled Tnufa Word (`.docx`) form and get structured, section-by-section review comments in Hebrew — highlighting gaps, inconsistencies, and unrealistic claims before you submit.

The form data is processed in memory and not stored.

## How it works
1. Upload the filled application (`.docx`).
2. The backend extracts each section's answer — **deterministically** from the official form's structure, with an **AI fallback** for non-standard documents.
3. A **single** OpenRouter call reviews all 11 textual sections against Tnufa's expectations, using a built-in per-section rubric.
4. The frontend renders the Hebrew comments per section.

## Tech stack
- Frontend: a single self-contained `index.html` (Hebrew, RTL), served by the backend.
- Backend: Flask (`app.py`) + `python-docx`.
- LLM: OpenRouter (`deepseek/deepseek-v4-pro`).
- Deploy: one Railway service (Flask serves both the page and the API).

## Endpoints
- `GET /` — the app.
- `GET /health` — `{"status":"ok"}`.
- `POST /review` — multipart `file` (`.docx`) → JSON `{section: [comments]}`.

## Backend environment
- `OPENROUTER_API_KEY` — OpenRouter API key (legacy misspelling `OPENEOPUTER_API_KEY` also accepted).
- `OPEN_ROUTER_MODEL` — model id (defaults to `deepseek/deepseek-v4-pro`).

## Repository layout
- `app.py` — Flask backend (extraction + review); serves `index.html`.
- `index.html` — frontend.
- `review_system_prompt.txt` / `instructions_form.json` — the Hebrew reviewer prompt and per-section review rubric.
- `requirements.txt` / `requirements-dev.txt` — runtime / dev dependencies.
- `Procfile` — gunicorn start command.
- `tests/` — pytest suite (stubbed LLM).
- `docs/` — project status and the reviewer rubric source.

## Run locally
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export OPENROUTER_API_KEY=sk-or-...
gunicorn app:app --bind 0.0.0.0:8000
# open http://localhost:8000
```
Run tests: `pytest`

## License
MIT — see [LICENSE](LICENSE).
