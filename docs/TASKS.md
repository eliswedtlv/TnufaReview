# TnufaReview — TASKS

Central task IDs live in `CCW PM/Tasks.md`. This is the repo-local view.

## Active
- None.

## Ops (Eli-owned, not a code task)
- Hosting cutover: single Railway service serving both API and frontend, custom domain, DNS (Cloudflare if that's where the domain lives), set `OPENROUTER_API_KEY` + `OPEN_ROUTER_MODEL` on Railway, retire GitHub Pages.

## Done
- **T-1133 — TNUFA-FRONTEND-REDESIGN** (frontend, `index.html`) — done 2026-07-09.
  Full visual redesign (done without the Refero MCP — it was not available in-session; designed from scratch). Removed the Tnufa-only modal + gating copy (any Word `.docx` accepted); kept `.docx`-only client guard, brand/trust signals, RTL, GitHub star button, and the `prettifyJSON` 11-section schema/titles/order. Switched the backend call to relative `/review` — **requires the single-service Flask deploy**, not GitHub Pages.
- **T-1132 — TNUFA-ANYDOCX-AI-EXTRACT-SERVE** (backend, `app.py`) — done 2026-07-08.
  Dropped the `is_tnufa_form` gate (any readable `.docx` accepted); replaced keyword extraction with an AI extraction step mapping the whole document into the fixed 11 sections; model defaults to `deepseek/deepseek-v4-pro`; env var resolves as `OPENROUTER_API_KEY` with legacy `OPENEOPUTER_API_KEY` fallback; Flask serves `index.html` at `/` + `/health` + `Procfile`. Folded in **T-1125** (OpenRouter migration committed). Tests in `tests/`.

## Backlog / later
- Extend review beyond the textual sections to the tasks list and budget (noted in the UI copy).
- Optional: restrict `CORS` once single-service is fully live.
