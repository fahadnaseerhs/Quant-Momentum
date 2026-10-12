# Task 03 findings → Task 04 defaults; statsmodels repair

**Date:** 2026-09-27
**Made by:** assistant (autonomous: defaults derived from Task 03 results; env repair needed to run the task)
**Status:** active

## 1. Defaults for Task 04, derived from Task 03 evidence
Full reasoning: Obsidian `Methodology/03 - Exploring Returns.md` §8.3.

| Decision | Evidence |
|---|---|
| σ for vol-scaling = EWMA λ = 0.94, **lagged one day**; 63-day rolling as a robustness check | Vol varies 3–5× over time; relative vol swings (BTC 1.2–9.7× SPY); rolling window has a 63-day "ghost" |
| Rank-based evaluation (Spearman IC); consider winsorising features at 1/99% | 21/21 assets fat-tailed; vol-scaling doesn't remove earnings-jump tails |
| Test ranking across the universe AND within blocks; MSTR → crypto block, DBC → oil block for class-level work | N_eff ≈ 3.9; MSTR–BTC 0.72; DBC–USO 0.91 |
| Lookback grid 5 / 10 / 21 / 63, chosen by Task 05's cross-sectional test, not by these ACFs | No own-return predictability at 1–10 days (9 robust hits / 210 ≈ chance) |
| Newey–West standard errors in all later tests | |r| clustering persists 20+ lags |

The universe itself (`src/universe.py`) is unchanged; class labels there stay as the user chose them.

## 2. Environment repair
`statsmodels` in `.venv` was incomplete (the `stats/`, `regression/` etc. subpackages were missing, as was pip's RECORD file, so pip couldn't reinstall it). I moved the broken folders to the session scratchpad (not deleted) and installed `statsmodels==0.15.0` fresh; all imports verified.

**Likely cause:** the project (including `.venv`) lives inside OneDrive, which can evict or partially sync files. Risk of recurrence. Option for the user: move `.venv` outside OneDrive, or mark the folder "Always keep on this device".
