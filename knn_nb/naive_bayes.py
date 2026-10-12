"""Gaussian Naive Bayes from scratch (NumPy only). Classes: 1 = up day, 0 = down day."""
from __future__ import annotations

import numpy as np


class GaussianNB:
    def __init__(self, var_floor: float = 1e-9):
        self.var_floor = var_floor

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GaussianNB":
        self.classes = np.array([0, 1])
        self.prior = np.array([(y == c).mean() for c in self.classes])
        self.mean = np.array([X[y == c].mean(0) for c in self.classes])
        self.var = np.array([X[y == c].var(0) + self.var_floor for c in self.classes])
        return self

    def log_joint(self, x: np.ndarray) -> np.ndarray:
        # log P(class) + sum_j log N(x_j | mean_cj, var_cj)  (logs avoid underflow)
        ll = -0.5 * (np.log(2 * np.pi * self.var) + (x - self.mean) ** 2 / self.var).sum(1)
        return np.log(self.prior) + ll

    def prob_up(self, x: np.ndarray) -> float:
        lj = self.log_joint(x)
        lj -= lj.max()
        p = np.exp(lj)
        return float(p[1] / p.sum())
