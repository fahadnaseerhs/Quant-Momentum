"""
Task 07 — Model 1: Linear regression by gradient descent (LEARNING RUN).

This script trains the from-scratch gradient-descent linear regression
(`src/linear_model.py`) so the *mechanics* of training are visible: weight
initialisation, the cost falling over epochs, the gradient-descent path, and
the fitted regression line.

>>> SCOPE WARNING <<<
This is an IN-SAMPLE learning run on the FULL feature matrix. It is NOT the
leakage-safe evaluation required by Task 07 (walk-forward, out-of-sample,
>=3-day embargo). Treat the metrics here as "does the machinery work and what
does the fit look like", not as evidence the model beats the baseline. The
walk-forward wrapper is the next step.

Outputs:
  reports/tables/07_linear_weights.csv
  reports/tables/07_metrics.csv
  reports/figures/07_g1_cost_curve.png
  reports/figures/07_g2_weight_trajectories.png
  reports/figures/07_g3_regression_line.png
  reports/figures/07_g4_gd_path.png
  reports/figures/07_g5_pred_vs_actual.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.linear_model import (
    LinearRegressionGD,
    information_coefficient,
    mae,
    rmse,
)

FEATURES_PATH = ROOT / "data" / "features" / "features.parquet"
FIG_DIR = ROOT / "reports" / "figures"
TBL_DIR = ROOT / "reports" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TBL_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "mom_5d", "mom_10d", "mom_21d", "mom_63d",
    "ewma_vol", "roll_vol_63d",
    "vsmom_5d", "vsmom_10d", "vsmom_21d", "vsmom_63d",
    "vol_ratio_20d",
    "relret_5d", "relret_10d", "relret_21d", "relret_63d",
]
TARGET = "fwd_ret_1d"
SINGLE_FEATURE = "vsmom_21d"   # strongest baseline signal (Task 06)

LR = 0.2          # stable region is lr < 2/lambda_max = 0.289 for these features
N_EPOCHS = 5000   # features are collinear (cond ~760) -> flat valley converges slowly


# ----------------------------------------------------------------------------- #
# Load & clean
# ----------------------------------------------------------------------------- #
feats = pd.read_parquet(FEATURES_PATH)
data = feats[FEATURE_COLS + [TARGET]].dropna()
X = data[FEATURE_COLS].to_numpy()
y = data[TARGET].to_numpy()
m, n = X.shape
print(f"Training rows: {m:,}  features: {n}  target: {TARGET}")
print(f"(dropped {len(feats) - m:,} rows with NaNs from warmup / last-day forward return)")


# ----------------------------------------------------------------------------- #
# A. Full 15-feature model
# ----------------------------------------------------------------------------- #
model = LinearRegressionGD(lr=LR, n_epochs=N_EPOCHS).fit(X, y)
y_hat = model.predict(X)

# Exact closed-form solution for comparison
w_cf, b_cf = LinearRegressionGD.normal_equation(X, y)

metrics = {
    "mae": mae(y, y_hat),
    "rmse": rmse(y, y_hat),
    "ic_in_sample": information_coefficient(y, y_hat),
    "final_cost_gd": model.history_["cost"][-1],
    "bias_gd": model.b_,
    "bias_closed_form": b_cf,
    "max_abs_weight_gap_vs_closed_form": float(np.max(np.abs(model.w_ - w_cf))),
    "lr": LR,
    "n_epochs": N_EPOCHS,
    "n_rows": m,
}
pd.Series(metrics).to_csv(TBL_DIR / "07_metrics.csv", header=False, float_format="%.6g")

weights_tbl = pd.DataFrame({
    "feature": FEATURE_COLS,
    "weight_gd": model.w_,
    "weight_closed_form": w_cf,
}).set_index("feature")
weights_tbl.to_csv(TBL_DIR / "07_linear_weights.csv", float_format="%.6g")

print("\n=== In-sample metrics (LEARNING RUN — not leakage-safe) ===")
for k, v in metrics.items():
    print(f"  {k:<36} {v:.6g}")
print("\n=== Learned weights (GD vs closed-form) ===")
print(weights_tbl.round(5).to_string())


# ----------------------------------------------------------------------------- #
# Graph 1 — cost vs epoch
# ----------------------------------------------------------------------------- #
cost = model.history_["cost"]
m_rows = y.shape[0]
# closed-form cost in the standardised space the model uses:
Xs = (X - model.mu_) / model.sd_
cf_pred = Xs @ w_cf + b_cf
cost_cf = float(np.sum((cf_pred - y) ** 2) / (2 * m_rows))

plt.figure(figsize=(10, 5.5))
plt.plot(cost, lw=1.6, label="gradient descent")
plt.axhline(cost_cf, color="crimson", ls="--", lw=1.2,
            label=f"closed-form minimum = {cost_cf:.3g}")
plt.xlabel("epoch")
plt.ylabel(r"cost  $J=\frac{1}{2m}\sum(\hat{y}-y)^2$")
plt.title("Task 07 — G1: cost falls as gradient descent learns (15 features)")
plt.legend()
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g1_cost_curve.png", dpi=130)
plt.close()


# ----------------------------------------------------------------------------- #
# Graph 2 — weight trajectories
# ----------------------------------------------------------------------------- #
w_hist = model.history_["weights"]  # (epochs+1, n)
plt.figure(figsize=(10, 6))
for j, name in enumerate(FEATURE_COLS):
    plt.plot(w_hist[:, j], lw=1.1, label=name)
plt.axhline(0, color="k", lw=0.6)
plt.xlabel("epoch")
plt.ylabel("weight value")
plt.title("Task 07 — G2: all 15 weights climbing from 0 to their fitted values")
plt.legend(fontsize=7, ncol=2, loc="best")
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g2_weight_trajectories.png", dpi=130)
plt.close()


# ----------------------------------------------------------------------------- #
# B. Single-feature model (for the clean line + GD-path pictures)
# ----------------------------------------------------------------------------- #
x1 = data[[SINGLE_FEATURE]].to_numpy()
m1 = LinearRegressionGD(lr=LR, n_epochs=N_EPOCHS).fit(x1, y)
x1s = (x1 - m1.mu_) / m1.sd_   # standardised single feature
x1s = x1s.ravel()


# ----------------------------------------------------------------------------- #
# Graph 3 — regression line
# ----------------------------------------------------------------------------- #
grid = np.linspace(x1s.min(), x1s.max(), 100)
line = m1.w_[0] * grid + m1.b_
plt.figure(figsize=(9, 6))
plt.scatter(x1s, y, s=6, alpha=0.15, label="observations")
plt.plot(grid, line, color="crimson", lw=2.2,
         label=f"fit:  ŷ = {m1.b_:.2e} + {m1.w_[0]:.2e}·x")
plt.xlabel(f"{SINGLE_FEATURE}  (standardised)")
plt.ylabel(TARGET)
plt.title(f"Task 07 — G3: fitted regression line, {SINGLE_FEATURE} → {TARGET}")
plt.legend()
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g3_regression_line.png", dpi=130)
plt.close()


# ----------------------------------------------------------------------------- #
# Graph 4 — gradient-descent path on the (w, b) cost surface
# ----------------------------------------------------------------------------- #
w_path = m1.history_["weights"].ravel()
b_path = m1.history_["bias"]

w_lo, w_hi = sorted([0.0, m1.w_[0]])
b_lo, b_hi = sorted([0.0, m1.b_])
pad_w = max(abs(m1.w_[0]), 1e-6) * 1.2 + 1e-6
pad_b = max(abs(m1.b_), 1e-6) * 1.5 + 1e-6
W = np.linspace(w_lo - pad_w, w_hi + pad_w, 120)
B = np.linspace(b_lo - pad_b, b_hi + pad_b, 120)
WW, BB = np.meshgrid(W, B)
# cost surface J(w, b) for the single standardised feature
JJ = np.empty_like(WW)
for i in range(WW.shape[0]):
    for j in range(WW.shape[1]):
        pred = WW[i, j] * x1s + BB[i, j]
        JJ[i, j] = np.sum((pred - y) ** 2) / (2 * len(y))

plt.figure(figsize=(9, 6.5))
cs = plt.contour(WW, BB, JJ, levels=25, cmap="viridis", linewidths=0.8)
plt.clabel(cs, inline=True, fontsize=6, fmt="%.2g")
plt.plot(w_path, b_path, "o-", color="crimson", ms=2.5, lw=1.0,
         label="gradient-descent path")
plt.scatter([w_path[0]], [b_path[0]], color="black", zorder=5, label="start (0, 0)")
plt.scatter([m1.w_[0]], [m1.b_], color="red", marker="*", s=160, zorder=5,
            label="minimum reached")
plt.xlabel("weight  w")
plt.ylabel("bias  b")
plt.title(f"Task 07 — G4: gradient descent walking downhill ({SINGLE_FEATURE})")
plt.legend(fontsize=8)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g4_gd_path.png", dpi=130)
plt.close()


# ----------------------------------------------------------------------------- #
# Graph 5 — predicted vs actual (full model) + IC
# ----------------------------------------------------------------------------- #
ic = metrics["ic_in_sample"]
plt.figure(figsize=(7.5, 7))
plt.scatter(y_hat, y, s=6, alpha=0.15)
lim = np.percentile(np.abs(np.concatenate([y_hat, y])), 99)
plt.plot([-lim, lim], [-lim, lim], "r--", lw=1, label="perfect prediction")
plt.xlim(-lim, lim)
plt.ylim(-lim, lim)
plt.xlabel("predicted  ŷ")
plt.ylabel("actual  fwd_ret_1d")
plt.title(f"Task 07 — G5: predicted vs actual (15 features)\n"
          f"in-sample IC = {ic:.3f}")
plt.legend()
plt.grid(True, ls=":", alpha=0.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "07_g5_pred_vs_actual.png", dpi=130)
plt.close()

print(f"\nSaved figures to {FIG_DIR}")
print(f"Saved tables  to {TBL_DIR}")
