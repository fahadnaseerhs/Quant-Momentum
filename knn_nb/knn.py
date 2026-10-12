"""K-NN from scratch (NumPy only). Regression-style: neighbours' next-day returns are averaged."""
from __future__ import annotations

import numpy as np


class KNN:
    def __init__(self, k: int = 50):
        self.k = k

    def fit(self, X: np.ndarray, y: np.ndarray) -> "KNN":
        # "lazy learner": training = standardise with train stats, then memorise
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-12
        self.X = (X - self.mu) / self.sd
        self.y = np.asarray(y, float)
        return self

    def neighbours(self, x: np.ndarray) -> np.ndarray:
        z = (x - self.mu) / self.sd
        d = np.sqrt(((self.X - z) ** 2).sum(1))      # Euclidean distance to every training day
        return self.y[np.argsort(d)[: self.k]]       # next-day returns of the K closest days

    def predict(self, x: np.ndarray) -> tuple[float, float, float]:
        """Returns (predicted return, spread of neighbours, share of neighbours that were up)."""
        nb = self.neighbours(x)
        return nb.mean(), nb.std(), (nb > 0).mean()
