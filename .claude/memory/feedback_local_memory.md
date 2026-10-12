---
name: feedback-local-memory
description: All memory + agentic decisions belong in the project-local `.claude/`, not the global `~/.claude/projects/` directory.
metadata:
  type: feedback
---

**Rule:** Keep every persistent memory file and every agentic-decision log inside the project's own `.claude/` folder at `C:\Users\USER\OneDrive\Desktop\Quant_ Momentum\.claude\`. Do **not** write new memories under `C:\Users\USER\.claude\projects\...` for this project.

**Why:** The user explicitly asked (2026-09-27) for memory to stay local with the project, so the knowledge travels with the folder and any autonomous decision made by the assistant is inspectable right next to the code.

**How to apply:**
- Session start → read `.claude/MEMORY.md` in the project root and the recent files in `.claude/decisions/`.
- New durable fact → new file in `.claude/memory/`, register it in `.claude/MEMORY.md`.
- Autonomous decision → new dated file in `.claude/decisions/` following the template in `.claude/README.md`.
- The global folder can be ignored for this project (it may still contain older entries from before this rule; do not rely on them as source of truth).
