# Adopt a project-local `.claude/` folder for memory and decisions

**Date:** 2026-09-27
**Made by:** user (with assistant implementing the structure)
**Status:** active

## Context

By default, Claude Code writes memory into a global directory at
`C:\Users\USER\.claude\projects\C--Users-USER-OneDrive-Desktop-Quant--Momentum\memory\`.
Yesterday I (assistant) followed that default and wrote the first batch of memories there. The user wants everything project-related to stay *with the project folder* instead — so it travels with the repo/notes, is inspectable next to the code, and doesn't hide autonomous decisions in a hidden global path.

## Options considered

- **Option A — Keep using the global `~/.claude/projects/...` directory.**
  - Pros: it's what Claude Code loads automatically at session start.
  - Cons: hidden from the user; doesn't travel with the folder; if the machine changes, the memory is orphaned; autonomous decisions live somewhere the user doesn't naturally look.
- **Option B — Create a project-local `.claude/` at the project root.**
  - Pros: memory + decisions live next to the work; visible; portable with the folder; user can review autonomous decisions directly; can be checked into git later if the project becomes a repo.
  - Cons: the assistant must be told at session start to load from here rather than the global path; slightly non-standard.

## Decision

**Option B.** Create `.claude/` inside the project root with the layout:

```
.claude/
├── README.md
├── MEMORY.md
├── memory/
└── decisions/
```

All future memory files and decision logs go here. The global folder is left in place but is no longer the source of truth.

## Rationale

The user was explicit: memory should be local, and *any agentic decision should also go there*. That maps cleanly onto a `memory/` + `decisions/` split. Making it a normal folder (not hidden inside `AppData`) lets the user review and edit it directly and keeps everything under version control if the project is later `git init`'d.

## Consequences

- Every future session must start by reading `.claude/MEMORY.md` and the recent files in `.claude/decisions/` from the project root, not from the global directory.
- The prior memory files at `C:\Users\USER\.claude\projects\C--Users-USER-OneDrive-Desktop-Quant--Momentum\memory\` are now stale copies. They have been re-created here; the global copies can be ignored or deleted at the user's discretion.
- The rule itself is recorded as durable feedback in [[feedback_local_memory]] so future sessions don't drift back to the global default.
- Any autonomous choice the assistant makes going forward (e.g., "picked yfinance over Alpha Vantage for data" when the user didn't specify) must be written up as a new dated file in `.claude/decisions/` using the template in `.claude/README.md`.
