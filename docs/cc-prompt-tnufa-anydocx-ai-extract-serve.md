# CC Prompt — TNUFA-ANYDOCX-AI-EXTRACT-SERVE (T-1132)

This repo has **no CLAUDE.md/AGENTS.md**. Read `README.md` and `docs/update_status.md` first. After completing all changes, update `docs/STATUS.md` by following `docs/update_status.md`, update `docs/TASKS.md` if task state changes, then run `git diff --stat`, commit, and push.

**Task ID:** T-1132 (folds in T-1125 — commit the uncommitted OpenAI→OpenRouter migration as part of this work)
**Project path:** `/Users/eliswed/Dropbox/Code/TnufaReview`
**Branch:** work on `main` (or a feature branch `t-1132-anydocx-ai-extract` if you prefer; this task and T-1133 touch different files — `app.py` vs `index.html` — so they can run in parallel).

---

## Context (read before coding)

- `app.py` — the entire backend. Note the **working tree is dirty**: `app.py` has an uncommitted migration from OpenAI (`gpt-5-mini`) to OpenRouter (`deepseek/deepseek-v4-pro`). That migration is correct and stays — you are building on top of it and committing it.
- `index.html` — single-file frontend (do **not** edit it in this task; T-1133 owns it). You only need it because Flask will now **serve** it.
- `requirements.txt` — `Flask`, `python-docx`, `Werkzeug`, `gunicorn`, `flask-cors`, `openai`. No new dependency is required for this task.
- `README.md` — project overview.

Key functions in `app.py` today:
- `require_env_var(name)` — raises at import if an env var is missing.
- Module-level: `OPENROUTER_MODEL = require_env_var("OPEN_ROUTER_MODEL")`, and the OpenAI client is built with `api_key=require_env_var("OPENEOPUTER_API_KEY")` (**typo — this is the startup bug**).
- `BASE_PROMPT` — the Hebrew reviewer prompt (do not change its review logic).
- `is_instruction_text(text)` — heuristic that flags form instructions/placeholders.
- `extract_from_docx_binary(binary)` — **keyword-based** extraction into 11 fixed sections via `section_keywords`. This is what we are replacing with AI extraction.
- `is_tnufa_form(file_bytes)` — **the gate** that requires the header `בקשת השקעה מקרן תנופה`. This gets removed.
- `call_llm_for_sections(sections, sections_to_review)` — one OpenRouter review call for a group of sections. Unchanged.
- `@app.route("/review")` — reads file → `is_tnufa_form` gate → `extract_from_docx_binary` → 3 concurrent review calls (`section_groups`) → merge → `desired_order` → `jsonify`.
- `@app.route("/")` — returns `{"status": "web extract v2"}`.

The 11 canonical section keys (order matters — the frontend renders in this exact order) are:
`executive_summary, the_need, the_product, team_and_capabilities, intellectual_property, technology_uniqueness_innovation, tasks_and_activities, market_clients_competition_business_model, grant_contribution_to_success, royalties, economic_and_technological_contribution`
Their fixed Hebrew `question` labels are defined in `extract_from_docx_binary`'s `json_structure` — **keep those exact labels**.

---

## What to build / change

### 1. Accept any readable `.docx` (remove the Tnufa-only gate)
- In `/review`, **remove the `is_tnufa_form(...)` gate**. Delete the `is_tnufa_form` function (it becomes dead) unless it is referenced elsewhere (it is not).
- Still validate the upload is a **readable `.docx`**: attempt `Document(io.BytesIO(file_data))`; if it raises, return `400` with a clear message, e.g. `{"error": "file must be a readable Word .docx document"}`.
- Scope note: only modern `.docx` is supported (python-docx). Do **not** add `.doc`/PDF handling.

### 2. Replace keyword extraction with **AI extraction** into the fixed 11 sections
Replace `extract_from_docx_binary`'s keyword-assignment approach with a two-step flow:

**a. Read ALL text from the docx** (new helper, e.g. `extract_all_text_from_docx(binary)`):
- Iterate `doc.element.body` in document order (as the current code does), collecting text from **paragraphs** (`CT_P` → `Paragraph`) and **table cells** (`CT_Tbl` → `Table` → rows/cells).
- Skip empty strings and the placeholder `"הזן טקסט כאן..."`. **Do not** keyword-filter and **do not** drop instruction text here — the AI needs the questions/instructions alongside answers to align them. (You may keep `is_instruction_text` in the file; it is no longer used for assignment but is harmless. Remove it only if you are confident nothing references it.)
- Return the ordered text as a single string (join with `"\n"`), preserving document order.

**b. AI-map the raw text into the 11 sections** (new helper, e.g. `ai_extract_sections(full_text)`):
- One OpenRouter call using the same `client` and `OPENROUTER_MODEL`, `response_format={"type": "json_object"}`.
- Prompt (Hebrew, system + user) must instruct the model to: read the whole document; extract **only the applicant's answers** (ignore instructions, placeholders, and the printed questions themselves); and map each answer to the correct one of the 11 canonical keys, using the fixed Hebrew `question` labels as the guide for what belongs where. If a section has no answer in the document, return an **empty string** for that key.
- Response contract: a single JSON object whose keys are exactly the 11 canonical keys, each value a **string** (the applicant's combined answer for that section). Enforce it: after parsing, coerce to a dict that always contains all 11 keys (missing → `""`, non-string → `str(...)`), and ignore any extra keys.
- Assemble the `sections` structure the review step expects: `{key: {"question": <fixed Hebrew label>, "answer": <extracted string>}}` for all 11 keys, using the fixed labels from `json_structure`.

**Keep `json_structure` (or an equivalent constant) as the single source of the 11 keys + Hebrew question labels.** The review pipeline (`section_groups`, `call_llm_for_sections`, merge, `desired_order`) stays **unchanged** and runs on the AI-extracted `sections`.

Net effect: `/review` now runs **4** OpenRouter calls total — 1 extraction call, then the existing 3 concurrent review calls.

### 3. Pin the model
- Keep reading `OPEN_ROUTER_MODEL` from env, but **default to `deepseek/deepseek-v4-pro`** when unset instead of crashing: `OPENROUTER_MODEL = os.environ.get("OPEN_ROUTER_MODEL", "deepseek/deepseek-v4-pro")`.

### 4. Fix the env-var typo (non-breaking)
- Resolve the API key as: prefer `OPENROUTER_API_KEY`, fall back to the legacy misspelled `OPENEOPUTER_API_KEY`. Raise only if **both** are missing. Do not log the key.
  ```python
  api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENEOPUTER_API_KEY")
  if not api_key:
      raise RuntimeError("Missing required environment variable: OPENROUTER_API_KEY")
  ```
- Update `README.md` env section to document `OPENROUTER_API_KEY` (note legacy fallback still accepted).

### 5. Serve the frontend from Flask (single Railway service)
We are consolidating to **one Railway service** that serves both the API and the page.
- Change `@app.route("/")` to **serve `index.html`** from the repo root, e.g. `send_file(os.path.join(app.root_path, "index.html"))` (import `send_file` from flask).
- Add `@app.route("/health")` returning `{"status": "ok"}` (keep a machine-checkable health endpoint).
- Leave `@app.route("/review")` path unchanged.
- Add a `Procfile` at repo root: `web: gunicorn app:app` (makes the Railway start command explicit and portable).
- Leave `CORS(app)` as-is for now (harmless; keeps the still-live GitHub Pages frontend working during the domain cutover). Do not tighten CORS in this task.

---

## What NOT to touch
- `index.html` — owned by T-1133.
- `BASE_PROMPT` review logic, `section_groups`, `desired_order`, the `/review` **response JSON shape** (keys + order must stay identical — the frontend depends on them).
- The 11 canonical keys and their Hebrew `question` labels.
- No new dependencies in `requirements.txt`.
- Do not change the OpenRouter base URL / headers.

---

## Edge cases
- Empty or answer-less document → extraction returns all-empty strings → review still runs and returns `"אין הערות"` per section. Must not 500.
- Extraction model returns malformed JSON, extra keys, missing keys, or non-string values → coerce/guard so all 11 keys exist as strings; never crash. On unrecoverable extraction failure, return a `500` with a clear message (mirror the existing group-failure error style).
- Non-`.docx` / corrupt file → `400` with the readable-docx message (do not 500).
- A `.docx` that is not a Tnufa form at all → still accepted; the AI maps whatever it can and leaves the rest empty (this is the intended new behavior).

## Regression checks
- A real Tnufa form still returns the same 11-key JSON in the same order, populated as before (spot-check that AI extraction fills the sections at least as well as the old keyword extraction on a known-good form).
- `/health` returns 200 JSON; `/` returns the HTML page (200, `text/html`).
- App **imports and boots without any env vars set** except the API key + model (model now defaults; key accepts either spelling).

## Tests to add/run
- Add lightweight tests (no live LLM call — monkeypatch/stub `client.chat.completions.create`):
  - `extract_all_text_from_docx` pulls text from both paragraphs and table cells, in order, skipping the placeholder.
  - `ai_extract_sections` output is coerced to exactly the 11 keys as strings even when the stub returns missing/extra/non-string keys.
  - `/review` with a stubbed extraction + review returns all 11 keys in `desired_order`.
  - Non-docx bytes → `/review` returns 400.
- If there is no test harness yet, add a minimal `tests/` with `pytest` and note it in `requirements.txt` **only as a dev note in the PR description** (do not add pytest to the runtime `requirements.txt` used by Railway unless the repo already installs dev deps separately — if unsure, keep tests runnable but don't change the deploy deps).
- Run whatever tests exist; report anything you could not run.

## Deployment (Eli-owned ops — do NOT execute, just leave notes in STATUS.md)
- Railway: single service, start command `gunicorn app:app` (via the new `Procfile`).
- Set env on Railway: `OPENROUTER_API_KEY` (correctly spelled), `OPEN_ROUTER_MODEL=deepseek/deepseek-v4-pro`.
- Add the custom domain in Railway → set the DNS CNAME (Cloudflare if that's where the domain lives) → once the redesigned page (T-1133) is served by Flask under the domain, retire GitHub Pages.

## Before commit
- Run `git diff --stat` and review it. Expect changes to `app.py`, `README.md`, new `Procfile`, new/updated `docs/STATUS.md` + `docs/TASKS.md`, and any `tests/`.
- Commit: `git add -A && git commit -m "T-1132: accept any .docx, AI section extraction, serve frontend from Flask, fix env-var + model default"`
- Push (unless told otherwise): `git push`.
- Final: confirm `docs/STATUS.md` and `docs/TASKS.md` reflect the shipped state.
