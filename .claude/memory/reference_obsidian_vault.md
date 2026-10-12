---
name: reference-obsidian-vault
description: Obsidian vault path used for user-facing project notes.
metadata:
  type: reference
---

The user keeps human-readable project notes in an Obsidian vault at:

`C:\Users\USER\OneDrive\Desktop\Quant_ Momentum\Quant_Momentum\`

The `.obsidian/` folder lives inside that directory. Notes are Markdown, and cross-note links use Obsidian's `[[Note Name]]` wiki-link syntax.

**Existing notes in the vault:**
- `Welcome.md` — Obsidian's default landing note.
- `00 - Project Introduction.md` — introduction covering purpose, pipeline, and success criteria.
- `Methodology/` — subfolder holding the conceptual/mathematical writeup for each pipeline task:
  - `_Methodology - README.md` — explains the folder's purpose.
  - `01 - Data Collection.md` — question, universe, methodology, environment, run guide, expected outcome for Task 1.

**How to apply:** When the user says "save this to Obsidian," "make a note," or asks for a human-facing writeup, put a `.md` file in the vault folder above. Use wiki links to related notes and to the scope doc (see [[reference_scope_document]]). Do **not** confuse the Obsidian vault (for human-facing prose) with `.claude/` (for assistant memory + decisions).

- `Technical Learning/` — concept notes, each concept explained ONCE (intuition → formulas): Prices/Returns/Stationarity, Volatility, Volatility Clustering, Return Distributions and Fat Tails, Correlation and Diversification, Autocorrelation - Momentum vs Reversal. Index: `_Technical Learning - README.md`.

- `Definitions/` — `Glossary A-Z.md` (every term, 1–2 lines + formula + link) and `Graph and Table Labels.md` (every axis label, colour, CSV column name, units rule: decimals). Index: `_Definitions - README.md`.
- `Figures/03/` — Task 03 figures copied here by the notebook so notes can embed them.

**Convention:** when a task introduces new terms or new output columns/labels, ADD them to `Definitions/Glossary A-Z.md` and `Definitions/Graph and Table Labels.md` in the same turn.

**Convention:** Methodology notes = what a task does and why; Technical Learning notes = the concepts. Task notes link to concept notes instead of re-explaining. When a new concept appears (e.g., IC, Sharpe, drawdown, walk-forward), add a Technical Learning note for it.

**Convention:** every task in the pipeline gets a matching Methodology note in `Quant_Momentum/Methodology/NN - <task name>.md`, following the structure of `01 - Data Collection.md` (question → methodology → environment → run guide → expected outcome).
