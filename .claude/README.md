# .claude — Local Project Memory & Decision Log

This folder keeps everything the assistant needs to remember about *this specific project* directly alongside the project files. It travels with the repo, and nothing important is stored in a hidden global directory somewhere else.

## Folder layout

```
.claude/
├── README.md          ← this file (how the folder works)
├── MEMORY.md          ← 1-line index of every memory file
├── memory/            ← persistent facts (who, what, why, where)
│   ├── user_*.md          User's profile, level, preferences
│   ├── feedback_*.md      Rules the user has told me to follow
│   ├── project_*.md       Project scope, phase, current state
│   └── reference_*.md     Pointers to external things (vault, docs)
└── decisions/         ← append-only log of agentic decisions
    └── YYYY-MM-DD-slug.md
```

## Rules for the assistant

1. **Load first.** At the start of every session, read `MEMORY.md` (index) and any file it points to that looks relevant to the current task. Also skim the most recent 2–3 files in `decisions/`.
2. **Write memory when learning something durable** — user preferences, project scope changes, corrections, non-obvious decisions. Follow the format in `MEMORY.md`.
3. **Log a decision when you make an autonomous call** — picking a library, dropping a feature, choosing an approach when the user didn't specify. One file per decision, dated, in `decisions/`.
4. **Never write ephemeral state here** — no in-progress task notes, no scratch output, no summaries of things the code or git already knows.
5. **Update, don't duplicate.** If a memory becomes stale, edit or delete it.

## Memory file format

```markdown
---
name: kebab-case-slug
description: one-line summary used for relevance ranking
metadata:
  type: user | feedback | project | reference
---

Body. For feedback/project entries, include:
**Why:** the reason behind the rule/fact
**How to apply:** when this kicks in during future work
```

Link between memories with `[[other-name]]`.

## Decision log format

Filename: `YYYY-MM-DD-short-slug.md` — most recent first when sorted.

```markdown
# <Short title of the decision>

**Date:** YYYY-MM-DD
**Made by:** assistant (autonomous) | user
**Status:** active | superseded by [[YYYY-MM-DD-other]] | reverted

## Context
What was going on that forced a choice.

## Options considered
- Option A — pros / cons
- Option B — pros / cons

## Decision
The choice made.

## Rationale
Why this option won.

## Consequences
What changes downstream because of this. What we now have to live with.
```
