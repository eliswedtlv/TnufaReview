# Handoff — Rebuild the TnufaReview reviewer prompt (strong model)

**You are a senior prompt engineer + Israel Innovation Authority "Tnufa" domain expert.** Your job: author the **best possible Hebrew reviewer prompt + per-section review criteria** for a tool that reviews filled Tnufa grant applications — by fully internalizing the source material below, then writing everything in your **own original wording**.

## Hard constraint — open-source safe (read first)
The output will be committed to a **public, MIT-licensed** repo. Therefore:
- **No verbatim quotes** from any IIA source (webinar/video transcripts, the IIA website text, or the official form's printed instruction sentences). Do not copy sentences or distinctive phrasings.
- **Distill** the requirements, expectations, and review heuristics into **original, paraphrased** criteria. Reproduce the *substance*, never the *text*.
- Facts and rules are fine to state (they aren't copyrightable) — e.g. budget/time caps, ineligible cost types, submission cadence — but phrase them yourself.
- No presenter names, no transcript excerpts, no pasted form-instruction blocks.
If in doubt, rewrite from scratch.

## What the tool does (runtime target)
- Founder uploads the Tnufa `.docx`; the backend extracts each section's answer into a JSON `application_form`.
- **One** LLM call (model: DeepSeek V4 Pro via OpenRouter) reviews **all 11 sections at once** and returns Hebrew review comments.
- Output is strict JSON: keys = the 11 canonical section IDs, each value = an array of Hebrew comment strings; `["אין הערות"]` when a section is solid. No prose outside the JSON.
- Audience: founders. Comments must be professional, specific, actionable — say what's missing / inconsistent / unrealistic / needs sharpening, never rewrite the answer for them.

## Canonical section IDs (must match exactly)
`executive_summary, the_need, the_product, team_and_capabilities, intellectual_property, technology_uniqueness_innovation, tasks_and_activities, market_clients_competition_business_model, grant_contribution_to_success, royalties, economic_and_technological_contribution`
(Plus a `general_instructions` block that applies across all sections.)

## Source material to read (in `TLVG Apps/Tnufaizer/`)
Read **all** of these, cross-reference them, and reconcile conflicts:
- Current best prompt (structure to improve on): `ACTIVE/Tnufa single section prompt.txt`
- IIA corpus (the knowledge to distill): `IIA_youtube_transcript.txt`, `IIA youtube 0 - 40.docx`, `Tnufa short video transcript .txt`, `IIA_materials_collected.txt`, `Tnufa from IIA site JSON.txt`, `Instructions by transcript JSON.txt`
- Existing structured criteria (starting point, improve + de-quote): `TNUFA FORM with full instrucitons JSON.txt`, `sections instructions JSON.txt`, `untitled folder/instructions_form.txt`
- Official form (for section structure + what each section asks — paraphrase only): `18.08.2025-בקשת-השקעה-במסלול-תנופה (1).docx`
- Quality examples (author's own writing — safe to reference, but keep separate): `Template replies.txt`

## Deliverables (Hebrew, drop-in ready)

**1. `review_system_prompt` (Hebrew).** A single reviewer prompt for the one-call architecture that:
- Establishes the expert reviewer role + Tnufa context (early-stage R&D, POC/prototype, limited budget & time, global-market tech, R&D not marketing/ops).
- Instructs: for each section, **first** check full coverage of that section's requirements (list gaps first), **then** assess depth, clarity, realism, feasibility within Tnufa, and **cross-section consistency/contradictions**.
- Permits cross-referencing and naming sections; forbids inventing facts, rewriting the founder's text, and quoting the guidelines.
- Enforces clean Hebrew (no Latin chars inside words, no broken words, no typos).
- Specifies the exact JSON output contract above.

**2. `instructions_form` (JSON, Hebrew).** For `general_instructions` + all 11 sections:
- `question` — short section title (paraphrased).
- `instructions` — what the section must cover (original wording).
- `max_length` — where the IIA implies one (else `null`).
- `review_guidelines` — an array of **specific, checkable** criteria in your own words: the real evaluation bar + the common failure modes reviewers catch. Aim for depth and completeness, section-appropriate.

**3. `changelog` (English, short).** What you strengthened vs. the current prompt, and how you ensured no source text was reproduced.

## Quality bar for the criteria
Make them concrete and testable, not generic platitudes. Ensure you capture the recurring failure patterns, e.g.: business/marketing initiative with no real technological novelty; Israel-only rather than global scope; scope/claims that don't fit ≤250K ₪ / ≤12 months; reliance on ineligible costs (salary, rent, overhead, travel); most of the plan not being R&D; no market validation; weak or unclear IP ownership; inconsistency across sections (same product/need/market/tech/tasks/IP); unrealistic performance promises for the stage. Cover each section's own specifics thoroughly.

## Output format
Return: the Hebrew `review_system_prompt`, then the Hebrew `instructions_form` JSON, then the English changelog. Nothing that reproduces IIA source text.
