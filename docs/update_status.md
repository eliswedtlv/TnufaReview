# How to update docs/STATUS.md

Whoever finishes a task in this repo updates `docs/STATUS.md` before committing.

Keep it short. `STATUS.md` should always answer "what is true right now" in under a screen.

Steps:
1. Update the **Last updated** date (YYYY-MM-DD).
2. Update the **Now / current state** section to reflect what actually shipped.
3. Move anything you finished out of "In progress" and into "Done recently" (keep only the last ~10).
4. If you added or changed backlog work, update `docs/TASKS.md` too.
5. Do not paste diffs or long logs here. One or two lines per change.

Conventions:
- This repo has **no CLAUDE.md/AGENTS.md** — `README.md` is the entry point.
- Specs / CC prompts live under `docs/` as `cc-prompt-<name>.md`.
- Backend: `app.py` (Flask). Frontend: single `index.html`. LLM via OpenRouter.
