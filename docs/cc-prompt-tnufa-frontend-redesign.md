# CC Prompt — TNUFA-FRONTEND-REDESIGN (T-1133)

This repo has **no CLAUDE.md/AGENTS.md**. Read `README.md` and `docs/update_status.md` first. After completing all changes, update `docs/STATUS.md` by following `docs/update_status.md`, update `docs/TASKS.md` if task state changes, then run `git diff --stat`, commit, and push.

**Task ID:** T-1133
**Project path:** `/Users/eliswed/Dropbox/Code/TnufaReview`
**Branch:** `main` (or `t-1133-frontend-redesign`). This task edits **only `index.html`**; the backend task T-1132 edits only `app.py`, so the two can run in parallel with no merge conflict.
**Uses:** the **Refero MCP** (connected in this Claude Code session) for design references. If the Refero MCP is not available in your session, stop and tell Eli rather than guessing at a design.

---

## Context (read before coding)

- `index.html` is the **entire frontend** — one file, inline `<style>` + inline `<script>`, Hebrew, `direction: rtl`.
- Current structure: header (h1 "TnufaReview" + slogan "קופיילוט לבקשת מענק תנופה" + intro paragraph) → privacy statement → upload section (drag/drop area, file input `accept=".docx"`, "העלו ובדקו" button, loading overlay with rotating messages, error/success message divs) → credit section (Eli Swed / TLVG + LinkedIn/X/GitHub SVG links) → result section (back button, copy button, `#resultContent`) → a **Tnufa-only modal** (`#modalOverlay`, title "טפסי תנופה בלבד").
- Key script pieces:
  - `uploadFile()` POSTs to a **hardcoded backend URL**: `https://web-production-17375.up.railway.app/review`.
  - `showError(message)` special-cases the strings `must be a .docx Tnufa application form` / `does not look like a Tnufa application form` → calls `showTnufaErrorModal()`.
  - `prettifyJSON(data)` renders the response. It contains `hebrewTitles` (key→Hebrew), `displayOrder` (the exact 11-section Hebrew order), `fieldLabels`, and formatting helpers. **This rendering + the 11 keys/titles/order must be preserved** — the backend contract is unchanged.
  - Drag/drop handler and `fileInput` change handler check `.docx`.

---

## What to build / change

### 1. Full visual redesign (primary goal)
Redesign the page into a modern, professional, trustworthy tool. This is a public-facing product for founders applying for a government innovation grant — the aesthetic should read as **credible, calm, and clean**, not flashy.

**Use the Refero MCP** to pull real design references before styling. Suggested reference queries: modern SaaS **file-upload / document-analysis** tools, clean **AI review/report** interfaces, minimal single-column marketing-to-app pages, and RTL/Hebrew-friendly layouts. Derive a cohesive system (spacing scale, type scale, color palette, elevation, radius, states) from the references — **do not copy any single design pixel-for-pixel**; produce an original layout.

Design direction / constraints:
- **RTL Hebrew stays** (`direction: rtl`), and the copy stays in Hebrew.
- Keep it a **single self-contained `index.html`** (inline CSS + JS). You may load web fonts from Google Fonts (Montserrat is already used) and keep the GitHub buttons script; **no build step, no external framework, no bundler.**
- Strong, obvious **upload affordance** as the hero action; clear loading state; highly **readable results** (the review output is long Hebrew prose per section).
- Accessible: sufficient contrast, focus states, keyboard-usable upload button, `alt`/`aria` where relevant, respects `prefers-reduced-motion` for any animation.
- Responsive: must look right on mobile (there is existing `@media (max-width: 768px)` — carry the responsive behavior forward).
- Preserve brand + trust signals: product name **TnufaReview**, slogan **"קופיילוט לבקשת מענק תנופה"**, the **privacy statement** (data not stored, open source on GitHub), the **credit block** (Eli Swed, CTO at TLVG + the LinkedIn/X/GitHub links), and the **GitHub star button**.

### 2. Remove the "Tnufa-only" messaging (backend now accepts any .docx)
- Upload subtext currently says **"טפסי תנופה בפורמט DOCX בלבד"** → change to indicate any Word document is accepted, e.g. **"קובץ Word בפורמט DOCX"**. Keep it truthful: still `.docx` only.
- **Remove the Tnufa-only modal** entirely: the `#modalOverlay` markup, `showTnufaErrorModal()`, `closeModal()`, and the special-case branch in `showError()` that routes the Tnufa-validation strings to the modal. Replace with normal inline error handling for whatever the backend returns.
- Keep a **generic** client-side guard that the selected file is `.docx` (the existing drag/drop + input checks), with a plain error message (e.g. "אנא בחר קובץ Word בפורמט DOCX"). The old "טפסי תנופה בלבד" copy must not survive anywhere.
- The header intro paragraph may stay Tnufa-focused (the tool is still about Tnufa applications) — just don't imply the upload must be the exact official form file.

### 3. Switch the backend call to a relative path (single-service)
- In `uploadFile()`, replace the hardcoded `https://web-production-17375.up.railway.app/review` with the **relative** URL `'/review'`. After the hosting cutover (T-1132 makes Flask serve this page), the page and API share an origin, so a relative path is correct and removes the brittle hardcoded host.
- **Dependency note:** relative `/review` only works when this page is served by the Flask backend (single Railway service). Until that cutover is deployed, the page must be tested against the single-service deploy, **not** GitHub Pages. Call this out in the PR/commit message.

### 4. Preserve the results rendering contract
- Keep `prettifyJSON` behavior: the `hebrewTitles` map, the exact `displayOrder` (11 sections), `fieldLabels`, list/section formatting, and the "אין הערות" handling. You may restyle the result markup/CSS classes, but the **section titles, their order, and the JSON keys consumed must remain identical**. Do not change the response shape you read.
- Keep the working features: rotating loading messages + "אל תרעננו את הדף" warning, copy-to-clipboard button (with the "הועתק!" confirmation), back button (returns to upload view and resets), smooth scroll-to-top on result.

---

## What NOT to touch
- `app.py` and the backend contract — owned by T-1132. Do not change the `/review` request/response shape.
- The 11 section **keys, Hebrew titles, and display order** inside `prettifyJSON`.
- Do not introduce a build system, framework, or external state/storage. No `localStorage`/`sessionStorage`.

## Edge cases
- Backend error responses (400/500 JSON with `error`/`message`) → show a clean inline error, no modal.
- Very long Hebrew section text → results remain scrollable/readable (keep the scroll container behavior).
- Mobile widths → upload, results, and the header/credit blocks all lay out correctly.
- Slow response (multi-minute) → loading state persists and the "do not refresh" warning shows.

## Regression checks
- Upload a valid `.docx` against the single-service backend → results render in the correct 11-section order with correct Hebrew titles, identical to today's content.
- Copy button copies the rendered text; back button resets to a clean upload view.
- No reference in the file to `web-production-17375.up.railway.app`, to `showTnufaErrorModal`, or to the "טפסי תנופה בלבד" copy.
- Keyboard + screen-reader basics work on the upload control.

## Tests / verification
- No JS test harness exists; verify manually. Before committing, at minimum:
  - Open the page and confirm layout on desktop + a ~375px mobile width (dev tools).
  - Confirm the `fetch` target is `'/review'`.
  - Grep the file to confirm the removed strings/functions are gone.
- If you can run the backend locally (single service), do a full end-to-end upload with a sample `.docx` and confirm the rendered result.

## Before commit
- Run `git diff --stat` (expect `index.html` + `docs/STATUS.md`/`docs/TASKS.md`).
- Commit: `git add -A && git commit -m "T-1133: redesign frontend (Refero), drop Tnufa-only gating, relative /review"`
- Push (unless told otherwise): `git push`.
- Final: update `docs/STATUS.md` and `docs/TASKS.md` to reflect the shipped redesign.
