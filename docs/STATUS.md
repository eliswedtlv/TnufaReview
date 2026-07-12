# TnufaReview — STATUS

**Last updated:** 2026-07-12 (T-1138 shipped)

## What it is
Web tool that reviews Israel Innovation Authority "Tnufa" grant applications. Founder uploads a Word (.docx) file → backend extracts the text → AI reviews each of the 11 Tnufa sections against Tnufa expectations → returns structured Hebrew comments per section.

## Now / current state
- **Backend** `app.py` (Flask) on OpenRouter (`deepseek/deepseek-v4-pro`). Accepts **any readable `.docx`** (Tnufa gate removed). Reviewer is now **v2** (T-1137): the prompt + per-section criteria live in `review_system_prompt.txt` + `instructions_form.json` (loaded once at startup, fail-fast if missing). Extraction is **AI-only** (T-1138): the deterministic `extract_sections_structural` path was removed because real filled forms are saved without heading styles, so it never mapped cleanly and `/review` always used the AI path anyway. Flow is now `extract_all_text_from_docx` (paragraphs + table cells, incl. the exec-summary answer inside a table cell) → `ai_extract_sections` → single review call (2 LLM calls total: extraction + review). Review is a **single** OpenRouter call over all 11 sections with `instructions_form` embedded. Section field is `applicant_answer`. Env var resolves as `OPENROUTER_API_KEY` with legacy `OPENEOPUTER_API_KEY` fallback; model defaults to `deepseek/deepseek-v4-pro` when unset.
- **Single service:** Flask serves `index.html` at `/`, `/health` returns `{"status":"ok"}`, `/review` unchanged. `Procfile` binds gunicorn to `0.0.0.0:$PORT` with 2 workers and a 180s timeout (T-1134) so Railway can reach it and long multi-minute OpenRouter reviews don't time out.
- **Frontend** single `index.html`, Hebrew RTL — **redesigned** (T-1133): warm-paper/evergreen visual system, Frank Ruhl Libre + Assistant fonts, accessible upload dropzone, staggered load. Tnufa-only messaging/modal removed (accepts any Word `.docx`). Backend call is now the **relative** `/review` — **requires the single-service deploy** (Flask serving the page); it will NOT work on GitHub Pages. `prettifyJSON` 11-section keys/titles/order preserved unchanged.
- **Hosting:** frontend on GitHub Pages, backend on Railway (cutover to single service pending, Eli-owned).
- Tests in `tests/` (pytest, stubbed LLM) — 8 passing. `pytest` is a dev-only dep, **not** in `requirements.txt`.

## In progress / planned
- Nothing active. Next up is the hosting cutover (below, Eli-owned) so the relative `/review` call goes live.

## Hosting cutover (Eli, ops — not executed by this task)
- Railway: single service, start command from `Procfile` (`gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180`).
- Set env on Railway: `OPENROUTER_API_KEY` (correctly spelled) + `OPEN_ROUTER_MODEL=deepseek/deepseek-v4-pro`.
- Add custom domain in Railway → set DNS CNAME (Cloudflare if the domain lives there) → once T-1133's page is served by Flask under the domain, retire GitHub Pages.

## Done recently
- **T-1138** drop deterministic extractor (`app.py`): removed `extract_sections_structural` + its helpers (and the now-unused `re` import) and the "maps cleanly" routing in `/review`. Real filled forms save without `Heading 1` styles, so the structural path always returned `clean=False` and the AI fallback ran anyway. AI extraction (`extract_all_text_from_docx` → `ai_extract_sections`, which reads paragraphs **and** table cells) is now the sole path. Response contract, prompt, and `instructions_form` unchanged. Tests: dropped the 3 structural tests + synthetic heading fixture, added a realistic no-heading fixture (exec-summary in a 2×1 table cell); 8 passing.
- **T-1137** v2 reviewer integration (`app.py`): externalized prompt + criteria to `review_system_prompt.txt` + `instructions_form.json` (startup load, fail-fast); dropped `BASE_PROMPT` + the 3-group `ThreadPoolExecutor` for a **single** all-11 review call with `instructions_form` embedded; `answer` → `applicant_answer`; added a **code-first** structural extractor with an AI-extraction fallback. Response contract unchanged. Tests: 11 passing.
- **T-1134** `Procfile` bind fix: gunicorn now binds `0.0.0.0:$PORT` (was defaulting to `127.0.0.1:8000`, unreachable on Railway) with `--workers 2 --timeout 180` so the single-service deploy passes its healthcheck and survives multi-minute OpenRouter calls.
- **T-1133** frontend redesign (`index.html`): new calm/credible visual system, removed the Tnufa-only modal + gating copy (any Word `.docx` accepted), switched the backend call from the hardcoded Railway host to relative `/review`. `prettifyJSON` 11-section contract untouched. **Note:** relative `/review` needs the single-service Flask deploy — not GitHub Pages.
- **T-1132** (folds in T-1125): committed OpenRouter/DeepSeek migration; dropped the Tnufa-only gate; replaced keyword extraction with AI extraction into the 11 sections; fixed the env-var typo (with legacy fallback); model default; Flask now serves `index.html` + `/health` + `Procfile`; added pytest tests.
