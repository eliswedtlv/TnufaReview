# CC Prompt — TNUFA-REVIEWER-V2-INTEGRATION (T-1137)

This repo has **no CLAUDE.md/AGENTS.md**. Read `README.md` and `docs/update_status.md` first. After completing all changes, update `docs/STATUS.md` per `docs/update_status.md`, update `docs/TASKS.md`, run `git diff --stat`, commit, and push.

**Task ID:** T-1137
**Project path:** `/Users/eliswed/Dropbox/Code/TnufaReview`
**Branch:** `main` (or `t-1137-reviewer-v2`).

## Goal
Replace the generic memory-only reviewer with the rebuilt v2 reviewer (prompt + per-section `instructions_form`), switch review to a **single** LLM call over all 11 sections, and make extraction **code-first with an AI fallback**. Source content is in `docs/reviewer-prompt-v2.md` (already reviewed/approved).

## Context — read before coding
- `app.py` — the whole backend. Today: `BASE_PROMPT` (generic), `ai_extract_sections` (LLM extraction into 11 sections, builds `{question, answer}`), `call_llm_for_sections` (one call per group), `/review` runs **3 concurrent group calls** via `section_groups` + `ThreadPoolExecutor`, merges, orders by `desired_order`, returns `{section: [comments]}`.
- `docs/reviewer-prompt-v2.md` — the approved deliverable. Section **1** is the Hebrew `review_system_prompt` (a fenced ```text block); section **2** is the Hebrew `instructions_form` (a fenced ```json block, `general_instructions` + the 11 canonical sections). Use these verbatim.
- `index.html` — **do not touch.** It consumes the response as `{section_key: [comments]}` in the 11-key order; that contract must stay identical.

The 11 canonical keys (order matters for the response):
`executive_summary, the_need, the_product, team_and_capabilities, intellectual_property, technology_uniqueness_innovation, tasks_and_activities, market_clients_competition_business_model, grant_contribution_to_success, royalties, economic_and_technological_contribution`

## What to build

### 1. Externalize the v2 content into loadable files
- Create **`review_system_prompt.txt`** at repo root = the exact Hebrew text from `docs/reviewer-prompt-v2.md` §1 (contents of the ```text block, no fences).
- Create **`instructions_form.json`** at repo root = the exact JSON from §2 (contents of the ```json block). It must `json.load` and contain `general_instructions` + the 11 keys.
- In `app.py`, load both once at startup: `REVIEW_SYSTEM_PROMPT = open(...).read()` and `INSTRUCTIONS_FORM = json.load(open(...))`, resolved relative to `app.root_path`. Remove the old `BASE_PROMPT` string.

### 2. Single review call (drop the 3 groups)
- Replace the `section_groups` + `ThreadPoolExecutor` + per-group calls with **one** OpenRouter call that reviews all 11 sections.
- Build the payload exactly as the v2 prompt expects:
  ```
  payload = {
    "application_form": sections,          # {key: {"question": <label>, "applicant_answer": <text>}} for all 11
    "sections_to_review": DESIRED_ORDER,   # all 11 keys, in canonical order
    "instructions_form": INSTRUCTIONS_FORM
  }
  user_content = REVIEW_SYSTEM_PROMPT + "\n" + json.dumps(payload, ensure_ascii=False)
  ```
- Keep `response_format={"type":"json_object"}`, the same system message ("return one JSON object only"), model `OPENROUTER_MODEL`.
- Parse the returned JSON, then order into the response via the existing `desired_order` (missing key → `["אין הערות"]`). Response shape returned to the frontend is **unchanged**: `{key: [comment strings]}` in canonical order.
- Keep the existing guard that rejects an extraction-format response (dict-valued `executive_summary`).

### 3. Field rename: `answer` → `applicant_answer`
The v2 prompt states each `application_form` section has `question` + `applicant_answer`. Change the section objects the app builds from `{"question":…, "answer":…}` to `{"question":…, "applicant_answer":…}` in **both** extraction paths below. (This is the field the prompt reads — get it right.)

### 4. Code-first extraction with AI fallback (hybrid)
Add a **deterministic** extractor for the official Tnufa form, and fall back to the existing LLM extractor only when the structure isn't recognized.

**Deterministic parser** (`extract_sections_structural(binary)`), built from the real form's structure:
- The form is a `.docx` whose body order is: a header table (contains the string `בקשת השקעה מקרן תנופה`), a Table-of-Contents (`toc 1`-styled paragraphs — skip), then the sections.
- Each of the 11 review sections is a **`Heading 1`** paragraph whose text matches (allow a leading number/whitespace, normalize) one of the canonical Hebrew labels. Non-review `Heading 1`s to skip: `פרטי המגיש והבקשה` and `נספחים…`.
- Within a section (until the next `Heading 1`): there are `Heading 2`/`Heading 3` sub-sections; **instruction text** lives in 1×1 tables and typically starts with one of: `תאר ופרט`, `יש להציג`, `יש לפרט`, `ציין האם`, `שים לב`, `ככל שרלוונט`, `הנחיה למילוי`, `יש להתייחס`, or contains `[1]`…`[2]` enumerations; the **founder's answer** is in `Norm`-styled paragraphs and/or answer table cells; the empty-answer placeholder is exactly `הזן טקסט כאן...`.
- Per section, the answer = concatenation (in document order) of founder text between this `Heading 1` and the next, **excluding**: sub-heading paragraphs, instruction tables, and the placeholder. Join with `\n\n`.
- Return `{key: {"question": <canonical label>, "applicant_answer": <text or "">}}` for all 11 keys.

**"Maps cleanly" check (code, deterministic — no LLM):**
- The doc contains the header string `בקשת השקעה מקרן תנופה`, **and** all 11 section `Heading 1` anchors are locatable by normalized label match.
- If clean → use the structural result. If not (missing header, or any of the 11 anchors not found) → call the existing `ai_extract_sections` on the whole-document text (fallback).
- Keep `ai_extract_sections` and `extract_all_text_from_docx`; update `ai_extract_sections` to emit `applicant_answer` (not `answer`).

Wire into `/review`: read the `.docx` (still 400 on unreadable) → `extract_sections_structural` → if clean use it, else AI fallback → single review call → order → return.

## What NOT to touch
- `index.html` and the response contract (`{key: [comments]}`, 11-key order).
- Model, OpenRouter base URL/headers, env-var handling, `/` `/health` routes, `Procfile`, CORS.
- The Hebrew content of `review_system_prompt.txt` / `instructions_form.json` — ship as authored.
- Do **not** commit the official Tnufa form docx (copyright — keep tests synthetic).

## Edge cases
- Recognized form but a section legitimately left blank → `applicant_answer: ""`, review still runs (returns `"אין הערות"` or a coverage comment). No crash.
- Unrecognized / re-arranged doc → AI fallback path.
- Review model returns malformed/missing/extra keys → coerce so all 11 keys exist as string-arrays; never 500 on a recoverable case; 500 with a clear message only on unrecoverable model failure (mirror existing error style).
- `instructions_form.json` / `review_system_prompt.txt` missing at startup → fail fast with a clear error.

## Tests (update `tests/`)
- Stub `client.chat.completions.create` (no live LLM). Update existing tests to the **single-call** flow and the `applicant_answer` field.
- `extract_sections_structural`: build a **synthetic** python-docx fixture that mimics the real structure (Heading 1 labels + a 1×1 instruction table + a `Norm` answer paragraph + a placeholder) and assert answers land under the right keys, instructions/placeholders are excluded, sub-headings are folded into the parent section.
- "Maps cleanly" true → structural path used (LLM extractor NOT called); missing an anchor / missing header → AI fallback path used.
- `/review`: one review call, payload contains `instructions_form` + all 11 in `sections_to_review`, `application_form` uses `applicant_answer`; response has all 11 keys in `desired_order`. Non-docx → 400.
- Run the suite; report anything not runnable.

## Before commit
- `json.load('instructions_form.json')` succeeds; keys == the 11 canonical + `general_instructions`.
- `git diff --stat` — expect `app.py`, new `review_system_prompt.txt`, new `instructions_form.json`, `tests/*`, `docs/STATUS.md`, `docs/TASKS.md`.
- Commit: `git add -A && git commit -m "T-1137: v2 reviewer (prompt + instructions_form), single review call, code-first extraction + AI fallback"`
- Push. Then update `docs/STATUS.md` + `docs/TASKS.md`.

## Deploy note (Eli ops — do not execute)
One review call now sends ~22K input tokens; still well within the gunicorn timeout. Nothing else changes on Railway.
