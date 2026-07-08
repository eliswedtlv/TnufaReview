# TnufaReview — TASKS

Central task IDs live in `CCW PM/Tasks.md`. This is the repo-local view.

## Active
- **T-1133 — TNUFA-FRONTEND-REDESIGN** (frontend, `index.html`)
  Full visual redesign using the Refero MCP; remove Tnufa-only messaging + modal; keep `.docx`-only, brand, RTL, and the `prettifyJSON` 11-section schema/order; switch the backend call to relative `/review`.
  Spec: `docs/cc-prompt-tnufa-frontend-redesign.md`

## Ops (Eli-owned, not a code task)
- Hosting cutover: single Railway service serving both API and frontend, custom domain, DNS (Cloudflare if that's where the domain lives), set `OPENROUTER_API_KEY` + `OPEN_ROUTER_MODEL` on Railway, retire GitHub Pages.

## Done
- **T-1132 — TNUFA-ANYDOCX-AI-EXTRACT-SERVE** (backend, `app.py`) — done 2026-07-08.
  Dropped the `is_tnufa_form` gate (any readable `.docx` accepted); replaced keyword extraction with an AI extraction step mapping the whole document into the fixed 11 sections; model defaults to `deepseek/deepseek-v4-pro`; env var resolves as `OPENROUTER_API_KEY` with legacy `OPENEOPUTER_API_KEY` fallback; Flask serves `index.html` at `/` + `/health` + `Procfile`. Folded in **T-1125** (OpenRouter migration committed). Tests in `tests/`.

## Backlog / later
- Extend review beyond the textual sections to the tasks list and budget (noted in the UI copy).
- Optional: restrict `CORS` once single-service is fully live.
