"""Tagesprofil-Clustering: Peer-Gruppierung der Standorte.

**Rolle (wichtig fürs Paper):** Dieses Clustering ist **ausschließlich Voraussetzung
für ARIMA** – ARIMA pro Einzelzähler skaliert nicht, daher wird ein ARIMA je Peer-Gruppe
ähnlicher Standorte trainiert. Es dient **nicht** dem Autoencoder (der wird pro Kategorie
trainiert, vgl. CLAUDE_patch_v4.md §1.1) und **nicht** der Anomalie-Diagnose – dafür ist
das distanzbasierte Segment-Clustering (`clustering_segments.py`) zuständig.

Einheit ist der **Standort**: geclustert werden die mittleren Tagesprofile der Sites
(96-dim, zeilen-normiert auf Form), Default k=3 (fachlich, konsistent mit `01_eda`).
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def _row_normalize(x: np.ndarray) -> np.ndarray:
    """Zeilenweise z-Normierung (Form statt Magnitude)."""
    return (x - x.mean(axis=1, keepdims=True)) / (x.std(axis=1, keepdims=True) + 1e-9)


class DailyProfileClusterer:
    """k-Means auf zeilen-normierten Site-Tagesprofilen → Peer-Gruppe je Standort.

    Parameters
    ----------
    k : Anzahl Peer-Gruppen (Default 3, fachlich begründet).
    seed : Reproduzierbarkeit.
    """

    def __init__(self, k: int = 3, seed: int = 42) -> None:
        self.k = k
        self.seed = seed
        self.kmeans_: KMeans | None = None
        self.columns_: pd.Index | None = None
        self.labels_: pd.Series | None = None

    def fit(self, profiles: pd.DataFrame) -> DailyProfileClusterer:
        """profiles: Index = site, Spalten = 96 Slot-Mittelwerte (oder beliebige Profildim)."""
        self.columns_ = profiles.columns
        xn = _row_normalize(profiles.to_numpy(dtype=float))
        self.kmeans_ = KMeans(n_clusters=self.k, n_init=10, random_state=self.seed).fit(xn)
        self.labels_ = pd.Series(self.kmeans_.labels_, index=profiles.index, name="peer_group")
        return self

    def _check_fitted(self) -> None:
        if self.kmeans_ is None or self.columns_ is None:
            raise RuntimeError("DailyProfileClusterer ist nicht gefittet – erst fit() aufrufen.")

    def predict(self, profiles: pd.DataFrame) -> pd.Series:
        """Peer-Gruppen-Label je Standort."""
        self._check_fitted()
        xn = _row_normalize(profiles[self.columns_].to_numpy(dtype=float))
        return pd.Series(self.kmeans_.predict(xn), index=profiles.index, name="peer_group")

    def save(self, path: str | Path) -> None:
        self._check_fitted()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> DailyProfileClusterer:
        return joblib.load(path)
