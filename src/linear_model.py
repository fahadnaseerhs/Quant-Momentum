"""Task 07 — Model 1: Linear regression by gradient descent (from scratch).

This module implements ordinary least-squares linear regression trained with
*batch gradient descent*, written out explicitly so every step of training is
visible:

    y_hat = b + X @ w                       (prediction)
    J     = (1 / 2m) * sum((y_hat - y)^2)   (mean-squared-error cost)
    dw    = (1 / m) * X.T @ (y_hat - y)      (gradient wrt weights)
    db    = (1 / m) * sum(y_hat - y)         (gradient wrt bias)
    w    -= lr * dw ;  b -= lr * db          (update)

The cost surface of OLS is convex, so gradient descent reaches the same global
minimum the closed-form normal equations give — we expose `normal_equation()`
so the two can be compared.

LEAKAGE NOTE
------------
`fit()` standardises features using the *training* mean/std only and reuses
them in `predict()`.  This class fits on whatever rows you hand it; it does NOT
enforce the walk-forward / embargo split.  That belongs to the caller (see the
planned walk-forward wrapper for the real out-of-sample evaluation).

Methodology: Quant_Momentum/Methodology/07 - Linear Regression.md (planned)
"""
from __future__ import annotations

import numpy as np


class LinearRegressionGD:
    """Linear regression trained with batch gradient descent.

    Parameters
    ----------
    lr : learning rate (alpha).
    n_epochs : number of full-batch gradient-descent steps.
    standardize : z-score features using training statistics before fitting.
    record_history : keep per-epoch cost / weight / bias snapshots for plotting.
    """

    def __init__(
        self,
        lr: float = 0.3,
        n_epochs: int = 800,
        standardize: bool = True,
        record_history: bool = True,
    ) -> None:
        self.lr = lr
        self.n_epochs = n_epochs
        self.standardize = standardize
        self.record_history = record_history

        # Learned parameters (set by fit)
        self.w_: np.ndarray | None = None   # shape (n_features,)
        self.b_: float = 0.0

        # Standardisation stats (set by fit, reused by predict)
        self.mu_: np.ndarray | None = None
        self.sd_: np.ndarray | None = None

        # Training history
        self.history_: dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------ #
    def _standardize(self, X: np.ndarray, fit: bool) -> np.ndarray:
        if not self.standardize:
            return X
        if fit:
            self.mu_ = X.mean(axis=0)
            self.sd_ = X.std(axis=0)
            self.sd_[self.sd_ == 0] = 1.0  # guard constant columns
        return (X - self.mu_) / self.sd_

    @staticmethod
    def _cost(y_hat: np.ndarray, y: np.ndarray) -> float:
        m = y.shape[0]
        return float(np.sum((y_hat - y) ** 2) / (2 * m))

    # ------------------------------------------------------------------ #
    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearRegressionGD":
        """Fit by gradient descent. X: (m, n_features), y: (m,)."""
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).ravel()
        Xs = self._standardize(X, fit=True)
        m, n = Xs.shape

        # ── Initialisation: weights = 0, bias = 0 (convex loss, no symmetry) ──
        self.w_ = np.zeros(n)
        self.b_ = 0.0

        if self.record_history:
            cost_hist = np.empty(self.n_epochs + 1)
            w_hist = np.empty((self.n_epochs + 1, n))
            b_hist = np.empty(self.n_epochs + 1)

        for epoch in range(self.n_epochs + 1):
            y_hat = Xs @ self.w_ + self.b_
            err = y_hat - y

            if self.record_history:
                cost_hist[epoch] = self._cost(y_hat, y)
                w_hist[epoch] = self.w_
                b_hist[epoch] = self.b_

            if epoch == self.n_epochs:
                break  # record final state, then stop (no update after last)

            dw = (Xs.T @ err) / m
            db = err.sum() / m
            self.w_ -= self.lr * dw
            self.b_ -= self.lr * db

        if self.record_history:
            self.history_ = {"cost": cost_hist, "weights": w_hist, "bias": b_hist}
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        Xs = self._standardize(X, fit=False)
        return Xs @ self.w_ + self.b_

    # ------------------------------------------------------------------ #
    @staticmethod
    def normal_equation(X: np.ndarray, y: np.ndarray, standardize: bool = True):
        """Exact closed-form OLS solution (bias + weights) for comparison.

        Returns (w, b) in the SAME (standardised, if requested) feature space
        as `fit`, so GD results can be overlaid on it.
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).ravel()
        if standardize:
            mu = X.mean(axis=0)
            sd = X.std(axis=0)
            sd[sd == 0] = 1.0
            X = (X - mu) / sd
        A = np.hstack([np.ones((X.shape[0], 1)), X])   # bias column
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        return coef[1:], float(coef[0])                 # w, b


# ---------------------------------------------------------------------- #
# Prediction-quality metrics
# ---------------------------------------------------------------------- #

def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_pred - y_true)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_pred - y_true) ** 2)))


def walk_forward_predict(
    data,
    feature_cols: list[str],
    target_col: str,
    *,
    horizon: int,
    lr: float = 0.2,
    n_epochs: int = 1500,
    initial_train: int = 252,
    step: int = 21,
    standardize: bool = True,
):
    """Expanding-window walk-forward out-of-sample prediction.

    Leakage defenses
    ----------------
    * Time-ordered: every test block comes strictly AFTER its training block.
    * Purge + embargo: a gap of `horizon` trading days separates the last
      training date from the first test date, so no training label (which
      looks `horizon` days ahead) overlaps the test window.

    Parameters
    ----------
    data : long DataFrame indexed by (date, ticker), SORTED, already dropna on
           `feature_cols + [target_col]`.
    horizon : label horizon in trading days (= purge/embargo gap).
    initial_train : trading days of history before the first prediction.
    step : trading days between refits (21 = monthly).

    Returns
    -------
    preds : pd.Series of out-of-sample predictions, indexed like the tested rows.
    folds : list of dicts, one per fold: train/test date ranges, n_train,
            and the per-epoch cost history (for plotting training convergence).
    """
    import pandas as pd

    dates_level = data.index.get_level_values("date")
    date_vals = dates_level.values
    unique_dates = pd.Index(dates_level.unique())          # sorted
    # row-start offset of each unique date (rows are contiguous per date)
    starts = np.searchsorted(date_vals, unique_dates.values, side="left")
    starts = np.append(starts, len(date_vals))

    X_all = data[feature_cols].to_numpy(dtype=float)
    y_all = data[target_col].to_numpy(dtype=float)

    pred = np.full(len(data), np.nan)
    folds = []

    n_dates = len(unique_dates)
    for test_pos in range(initial_train, n_dates, step):
        train_end_pos = test_pos - horizon          # purge/embargo gap
        if train_end_pos <= 0:
            continue
        tr_lo, tr_hi = 0, starts[train_end_pos]
        te_lo = starts[test_pos]
        te_hi = starts[min(test_pos + step, n_dates)]
        if tr_hi - tr_lo < initial_train or te_hi <= te_lo:
            continue

        model = LinearRegressionGD(
            lr=lr, n_epochs=n_epochs, standardize=standardize, record_history=True
        ).fit(X_all[tr_lo:tr_hi], y_all[tr_lo:tr_hi])
        pred[te_lo:te_hi] = model.predict(X_all[te_lo:te_hi])

        folds.append({
            "train_start": unique_dates[0],
            "train_end": unique_dates[train_end_pos - 1],
            "test_start": unique_dates[test_pos],
            "test_end": unique_dates[min(test_pos + step, n_dates) - 1],
            "n_train": tr_hi - tr_lo,
            "cost": model.history_["cost"],
        })

    preds = pd.Series(pred, index=data.index, name=f"pred_{target_col}").dropna()
    return preds, folds


def information_coefficient(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Pearson correlation of predictions with realised returns (the signal's
    'IC' — the number that matters for a trading model)."""
    y_true = np.asarray(y_true, float).ravel()
    y_pred = np.asarray(y_pred, float).ravel()
    if y_true.std() == 0 or y_pred.std() == 0:
        return float("nan")
    return float(np.corrcoef(y_true, y_pred)[0, 1])
