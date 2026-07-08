# TnufaReview — STATUS

**Last updated:** 2026-07-08 (T-1132 shipped)

## What it is
Web tool that reviews Israel Innovation Authority "Tnufa" grant applications. Founder uploads a Word (.docx) file → backend extracts the text → AI reviews each of the 11 Tnufa sections against Tnufa expectations → returns structured Hebrew comments per section.

## Now / current state
- **Backend** `app.py` (Flask) on OpenRouter (`deepseek/deepseek-v4-pro`). Accepts **any readable `.docx`** (Tnufa gate removed). Extraction is now **AI-based**: read all text → one OpenRouter call maps it into the fixed 11 sections → 3 concurrent review calls (4 LLM calls total). Env var resolves as `OPENROUTER_API_KEY` with legacy `OPENEOPUTER_API_KEY` fallback; model defaults to `deepseek/deepseek-v4-pro` when unset.
- **Single service:** Flask serves `index.html` at `/`, `/health` returns `{"status":"ok"}`, `/review` unchanged. `Procfile` (`web: gunicorn app:app`) added.
- **Frontend** single `index.html`, Hebrew RTL. Still calls a **hardcoded** Railway URL until T-1133 switches it to relative `/review`.
- **Hosting:** frontend on GitHub Pages, backend on Railway (cutover to single service pending, Eli-owned).
- Tests in `tests/` (pytest, stubbed LLM) — 5 passing. `pytest` is a dev-only dep, **not** in `requirements.txt`.

## In progress / planned
- **T-1133** frontend: full **redesign** (Refero MCP), remove Tnufa-only messaging/modal, switch backend call to **relative `/review`**. Spec: `docs/cc-prompt-tnufa-frontend-redesign.md`.

## Hosting cutover (Eli, ops — not executed by this task)
- Railway: single service, start command `gunicorn app:app` (via `Procfile`).
- Set env on Railway: `OPENROUTER_API_KEY` (correctly spelled) + `OPEN_ROUTER_MODEL=deepseek/deepseek-v4-pro`.
- Add custom domain in Railway → set DNS CNAME (Cloudflare if the domain lives there) → once T-1133's page is served by Flask under the domain, retire GitHub Pages.

## Done recently
- **T-1132** (folds in T-1125): committed OpenRouter/DeepSeek migration; dropped the Tnufa-only gate; replaced keyword extraction with AI extraction into the 11 sections; fixed the env-var typo (with legacy fallback); model default; Flask now serves `index.html` + `/health` + `Procfile`; added pytest tests.
