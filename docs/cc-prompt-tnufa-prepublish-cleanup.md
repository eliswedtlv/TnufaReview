# CC Prompt — T-1143 TNUFA-PREPUBLISH-CLEANUP

Read README.md and docs/update_status.md first. After completing all changes, update docs/STATUS.md by following docs/update_status.md, update docs/TASKS.md if task state changes, commit and push the changes.

**Task ID:** T-1143
**Project path:** `/Users/eliswed/Dropbox/Code/TnufaReview`
**Branch:** `main` (push directly, no PR flow)

## Context

TnufaReview is live at https://tnufareview.com/ as a single Railway service: Flask (`app.py`) serves the self-contained `index.html` at `/` plus `POST /review` and `GET /health`. The repo is about to be announced as open source. A pre-publish review found a batch of small correctness/hygiene issues. This is one cohesive cleanup pass — no feature work.

Key facts about the code as it is now:

- `app.py` (~350 lines): `extract_all_text_from_docx` → `ai_extract_sections` (1 OpenRouter call) → `call_llm_review` (1 OpenRouter call) → `order_review` coercion. Client is the `openai` SDK pointed at `https://openrouter.ai/api/v1`.
- Live model on Railway is `google/gemini-3.1-flash-lite` via env `OPEN_ROUTER_MODEL`; the **code default** is still `deepseek/deepseek-v4-pro` (a slow reasoning model that made reviews take 8–10 min and 502).
- Response contract of `/review`: JSON object with exactly the 11 canonical keys in `DESIRED_ORDER`, each an array of Hebrew comment strings. The frontend `prettifyJSON` renders these. **This contract must not change.**
- Tests: `tests/test_app.py` (9 passing, stubbed LLM), `tests/conftest.py` sets `OPENROUTER_API_KEY=test-key` at import.

## Files to inspect

- `app.py` (whole file)
- `index.html` — only the `<script>` block, specifically `prettifyJSON` (~lines 861–1023)
- `requirements.txt`, `README.md`
- `tests/test_app.py`, `tests/conftest.py`
- `docs/reviewer-prompt-v2.md` — first 5 lines only

## What to change

### 1. `app.py` — stale site URL
`OPENROUTER_SITE_URL = "https://eliswedtlv.github.io/TnufaReview/"` → `"https://tnufareview.com/"`. (GitHub Pages is retired.)

### 2. `app.py` — OpenRouter attribution header
The default header `"X-OpenRouter-Title"` is not what OpenRouter specifies; the correct header is `"X-Title"`. Rename the key (value stays `OPENROUTER_APP_TITLE`).

### 3. `app.py` — upload size cap
Add after `app = Flask(__name__)`:

```python
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB — a filled Tnufa form is well under this
```

Flask returns an HTML 413 by default, but the frontend expects JSON on every `/review` response (it does `response.json()` and shows `data.message || data.error`). Add a JSON error handler in the same error shape used elsewhere in `app.py`:

```python
@app.errorhandler(413)
def payload_too_large(e):
    return jsonify({"error": "file too large (max 10MB)"}), 413
```

### 4. `app.py` + `README.md` — model default
`OPENROUTER_MODEL_DEFAULT = "deepseek/deepseek-v4-pro"` → `"google/gemini-3.1-flash-lite"` (what production actually runs; the deepseek default gives cloners the broken 8-min experience). Update README: the "Tech stack" LLM line and the `OPEN_ROUTER_MODEL` default in "Backend environment". Also update the comment in `tests/conftest.py` that names the old default.

### 5. Drop `flask-cors`
The service is same-origin (Flask serves the page and the API), so CORS is unnecessary — and the pinned `flask-cors==4.0.0` has a known CVE (fixed in 4.0.1). Remove entirely:

- `app.py`: delete `from flask_cors import CORS` and `CORS(app)`.
- `requirements.txt`: delete the `flask-cors==4.0.0` line.

Do NOT add any replacement CORS mechanism.

### 6. `app.py` + `README.md` — drop the legacy env-var typo fallback
Remove the `OPENEOPUTER_API_KEY` fallback (internal history; Railway env is now correctly spelled):

```python
api_key = os.environ.get("OPENROUTER_API_KEY")
```

Keep the fail-fast `RuntimeError` if missing. Remove the "(legacy misspelling … also accepted)" parenthetical from README's "Backend environment" section, and the stale comment above the lookup.

### 7. `app.py` — specific exception
In `extract_all_text_from_docx`, `raise Exception(...)` → `raise ValueError(...)` (message unchanged). `/review` already pre-validates the docx, and its outer `except Exception` still catches this — behavior identical.

### 8. `index.html` — `prettifyJSON` dead-key cleanup + title escaping
The backend (`order_review`) guarantees exactly the 11 canonical snake_case keys — nothing else can arrive. In `prettifyJSON`:

- In `hebrewTitles`, keep ONLY the 11 canonical snake_case keys (`executive_summary` … `economic_and_technological_contribution`); delete all legacy/alias entries (`'Executive Summary'`, `'product'`, `'work_plan'`, `'budget'`, `'Competition'`, etc.).
- Keep `displayOrder`, the `dataByHebrewTitle` ordering pass, and the unknown-key fallback loop as-is (defensive rendering is fine).
- In `processSection`, escape the title: `html += `<div class="section-title">${escapeHtml(hebrewTitle)}</div>`;` — the fallback path passes a raw key as the title, so it must go through `escapeHtml` like every other value. (`escapeHtml` is already defined above it in the same closure.)
- `fieldLabels` may stay unchanged.

No other frontend change — no CSS, copy, layout, or flow edits.

### 9. `docs/reviewer-prompt-v2.md` — dead reference
Line ~3 references `docs/handoff-reviewer-prompt-rebuild.md`, which was deleted in the repo cleanup. Reword that sentence so it doesn't point at a nonexistent file (e.g. "Deliverables: Hebrew `review_system_prompt`, Hebrew `instructions_form` JSON, English changelog."). Change only that sentence.

## What NOT to touch

- `review_system_prompt.txt`, `instructions_form.json` — the reviewer content is frozen.
- The `/review` response contract (`{key: [comments]}`, 11 canonical keys, order) and `DESIRED_ORDER` / `SECTION_STRUCTURE`.
- Extraction/review flow, prompts, timeouts, logging (T-1140), `Procfile`, favicon/OG assets and routes (T-1141), fonts (T-1142).
- No rate limiting, no auth, no new dependencies.
- `LICENSE`, `.gitignore`.

## Tests

All existing tests must pass. Update/add:

- `tests/conftest.py`: update the model-default comment (item 4).
- New test: `POST /review` with a payload larger than 10MB returns **413** and a JSON body containing `"error"`. Build it without allocating a real 10MB docx if possible (e.g. `data={"file": (io.BytesIO(b"x" * (11 * 1024 * 1024)), "big.docx")}` is fine — it's memory-only).
- New test (frontend contract is untestable in pytest — skip; instead): assert `app.config["MAX_CONTENT_LENGTH"] == 10 * 1024 * 1024`.
- Verify no test imports or references `flask_cors` or `OPENEOPUTER_API_KEY`.

Run: `OPENROUTER_API_KEY=test-key python -m pytest -q` → expect 11 passing (9 existing + 2 new).

## Regression checks

- `python -c "import app"` succeeds with `OPENROUTER_API_KEY=test-key` set (startup file loads + client init still work).
- `grep -rn "flask_cors\|OPENEOPUTER\|eliswedtlv.github.io\|X-OpenRouter-Title\|deepseek/deepseek-v4-pro" app.py index.html requirements.txt README.md tests/` returns nothing.
- `grep -c "work_plan\|'budget'\|'Competition'" index.html` returns 0.
- The 11 canonical keys still render: quick manual check that `prettifyJSON` maps `executive_summary` → `סיכום מנהלים` etc. (the existing key strings must be byte-identical to `DESIRED_ORDER`).

## Commit

1. Review `git diff --stat` before committing — expect changes only in: `app.py`, `index.html`, `requirements.txt`, `README.md`, `tests/test_app.py`, `tests/conftest.py`, `docs/reviewer-prompt-v2.md`, `docs/STATUS.md`, `docs/TASKS.md`.
2. `git add -A && git commit -m "T-1143: pre-publish cleanup — site URL, X-Title header, 10MB upload cap + JSON 413, model default gemini-3.1-flash-lite, drop flask-cors + legacy env fallback, prettifyJSON dead keys + title escaping, docs dead link"`
3. `git push`

REMINDER: Do not forget to update docs/STATUS.md (per docs/update_status.md) and docs/TASKS.md (move T-1143 to Done), commit, and push.
