---
name: project-current-phase
description: Current phase — Task 04 (Feature Engineering) done; next is Task 05 Signal Analysis (Spearman IC, momentum buckets).
metadata:
  type: project
---

**Current phase (as of 2026-10-02):** Tasks 01–04 done. Next: **Task 05 — Signal Analysis** (cross-sectional ranking, Spearman IC, momentum buckets).

**Done:**
- Task 01 fetch -> `data/raw/`; Task 02 cleaning -> `data/processed/` (1439 NYSE days × 21; GOLD->B fix).
- Task 03: `src/eda.py`, `notebooks/03_explore_returns.ipynb` (the notebook itself is the source of truth now — edit its cells directly; time-series charts use the `format_time_axis` helper and `LogLabel` formatter defined in its setup cell), 16 figures in `reports/figures/` + copied to `Quant_Momentum/Figures/03/`, 10 tables in `reports/tables/`.
- Task 04: `src/features.py` (pure functions), `scripts/04_build_features.py` (orchestrator) -> `data/features/features.parquet` (long-format: 28780 rows × 17 cols, index = date × ticker, 20 tradeables).
- Obsidian: Methodology 01–04, Technical Learning folder (6 concept notes).

**Key Task 03 findings (drove Task 04):** fat tails everywhere; vol clustering (18/21 by |r|); N_eff ≈ 3.9 (blocks: crypto+MSTR, oil+DBC, gold, bonds, US equities); NO own-return autocorrelation at 1–10 days (≈ chance level); correlation spikes in stress. Defaults in `decisions/2026-09-27-task03-findings-and-env-repair.md`.

**Task 04 feature matrix columns:**
- Momentum: `mom_5d`, `mom_10d`, `mom_21d`, `mom_63d`
- Volatility: `ewma_vol` (EWMA λ=0.94, lagged 1 day), `roll_vol_63d` (robustness)
- Vol-scaled momentum: `vsmom_5d`, `vsmom_10d`, `vsmom_21d`, `vsmom_63d`
- Volume: `vol_ratio_20d`
- Relative return: `relret_5d`, `relret_10d`, `relret_21d`, `relret_63d`
- Forward targets (labels only): `fwd_ret_1d`, `fwd_ret_3d`
- All features winsorised at 1/99 percentile. No inf values.

**Still undecided by user:** target horizon (1-day vs 3-day), prediction model.

**Environment caveat:** `.venv` sits inside OneDrive; statsmodels was found corrupted and reinstalled. If imports fail oddly, suspect OneDrive sync first.

**How to apply:** Task 05 tests which features actually predict returns. Compute Spearman IC between feature ranks and forward-return ranks, test within asset-class blocks, and build momentum buckets. Follow the Methodology-note-first workflow.
