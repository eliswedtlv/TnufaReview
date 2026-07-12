# TnufaReview — TASKS

Central task IDs live in `CCW PM/Tasks.md`. This is the repo-local view.

## Active
- None.

## Ops (Eli-owned, not a code task)
- Hosting cutover: single Railway service serving both API and frontend, custom domain, DNS (Cloudflare if that's where the domain lives), set `OPENROUTER_API_KEY` + `OPEN_ROUTER_MODEL` on Railway, retire GitHub Pages.

## Done
- **T-1138 — TNUFA-EXTRACTION-SIMPLIFY** (backend, `app.py`) — done 2026-07-12.
  Removed the deterministic `extract_sections_structural` extractor (+ its helpers and the now-orphaned `re` import) and the "maps cleanly" routing in `/review`. Real filled Tnufa forms are exported without `Heading 1` styles, so the structural path always returned `clean=False` and `/review` always fell through to the AI extractor. New flow: validate readable `.docx` (400 if not) → `extract_all_text_from_docx` (paragraphs + table cells) → `ai_extract_sections` → single all-11 review call → order via `desired_order`. Response contract, v2 prompt, and `instructions_form` unchanged. Tests: dropped the 3 structural tests + synthetic heading fixture; added a realistic no-heading fixture (exec-summary answer inside a 2×1 table cell) verifying the cell text is captured; 8 passing.
- **T-1137 — TNUFA-REVIEWER-V2-INTEGRATION** (backend, `app.py`) — done 2026-07-12.
  Integrated the v2 reviewer into `app.py`: externalized the prompt + per-section criteria to `review_system_prompt.txt` and `instructions_form.json` (loaded once at startup, fail-fast if missing); dropped `BASE_PROMPT` + the 3-group `ThreadPoolExecutor` review in favour of a **single** OpenRouter call over all 11 sections with `instructions_form` embedded; renamed the section field `answer` → `applicant_answer` in both extraction paths; added a **code-first structural extractor** (`extract_sections_structural`) for the official form with an AI-extraction **fallback** when the doc doesn't map cleanly. Response contract (`{key: [comments]}`, 11-key canonical order) unchanged. Tests updated (single-call flow, structural extractor with a synthetic fixture) — 11 passing.
- **T-1136 — TNUFA-REVIEWER-PROMPT-V2** (content) — done 2026-07-12, shipped by T-1137.
  Rebuilt Hebrew reviewer prompt + per-section review criteria authored from the IIA corpus (original wording, open-source safe). Deliverable `docs/reviewer-prompt-v2.md`; now integrated into the app as `review_system_prompt.txt` + `instructions_form.json`.
- **T-1133 — TNUFA-FRONTEND-REDESIGN** (frontend, `index.html`) — done 2026-07-09.
  Full visual redesign (done without the Refero MCP — it was not available in-session; designed from scratch). Removed the Tnufa-only modal + gating copy (any Word `.docx` accepted); kept `.docx`-only client guard, brand/trust signals, RTL, GitHub star button, and the `prettifyJSON` 11-section schema/titles/order. Switched the backend call to relative `/review` — **requires the single-service Flask deploy**, not GitHub Pages.
- **T-1132 — TNUFA-ANYDOCX-AI-EXTRACT-SERVE** (backend, `app.py`) — done 2026-07-08.
  Dropped the `is_tnufa_form` gate (any readable `.docx` accepted); replaced keyword extraction with an AI extraction step mapping the whole document into the fixed 11 sections; model defaults to `deepseek/deepseek-v4-pro`; env var resolves as `OPENROUTER_API_KEY` with legacy `OPENEOPUTER_API_KEY` fallback; Flask serves `index.html` at `/` + `/health` + `Procfile`. Folded in **T-1125** (OpenRouter migration committed). Tests in `tests/`.

## Backlog / later
- Extend review beyond the textual sections to the tasks list and budget (noted in the UI copy).
- Optional: restrict `CORS` once single-service is fully live.
