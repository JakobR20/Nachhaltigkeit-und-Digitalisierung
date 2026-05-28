"""Segment-Clustering als distanzbasierte Diagnose-Schicht.

**Rolle (wichtig fürs Paper):** Dies ist die **Diagnose-Schicht für ALLE Methoden**
(Z-Score, ARIMA, Autoencoder). Sie beantwortet „ist dieser Segment-Tag untypisch und
welche Tageszeit?" – methoden-agnostisch, weil sie nur auf den Segment-Features arbeitet.

Statt der Cluster-**Zugehörigkeit** wird die **Distanz zum nächsten Cluster-Zentrum** als
kontinuierliches Auffälligkeitsmaß verwendet. Damit ist die exakte Clusterzahl
niedrig-sensitiv (das Signal trägt die Distanz, nicht das Label) – die Silhouette-Tendenz
zu k=2 ist daher unkritisch. Der Score ist kontinuierlich und damit im Methodenvergleich
(Schritt 11) direkt neben Z-Score- und ARIMA-Residuum stellbar.

Pro Segment: eigener `StandardScaler` (getrennte Wertebereiche je Tageszeit) + `KMeans` +
Perzentil-Schwelle aus den **Train**-min-Distanzen. Fit nur auf dem Train-Slice und ohne
`*_incomplete`-Tage; gescort werden alle Jahre.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class SegmentClusterer:
    """Distanzbasierte Diagnose je Tageszeit-Segment.

    Parameters
    ----------
    segments : Segmentnamen (z. B. ["nachts", "vormittag", ...]).
    features : Feature-Suffixe je Segment (z. B. ["mean", "max", "std", "slope"]).
    k_per_segment : Clusterzahl je Segment (aus config ``k_final_per_segment``).
    threshold_percentile : Perzentil der Train-min-Distanzen als Anomalie-Schwelle.
    seed : Reproduzierbarkeit.
    """

    def __init__(
        self,
        segments: list[str],
        features: list[str],
        k_per_segment: dict[str, int],
        threshold_percentile: float = 99.0,
        seed: int = 42,
    ) -> None:
        self.segments = segments
        self.features = features
        self.k_per_segment = k_per_segment
        self.threshold_percentile = threshold_percentile
        self.seed = seed
        self.scalers_: dict[str, StandardScaler] = {}
        self.kmeans_: dict[str, KMeans] = {}
        self.thresholds_: dict[str, float] = {}

    def _cols(self, segment: str) -> list[str]:
        return [f"{segment}_{f}" for f in self.features]

    def fit(self, features: pd.DataFrame, train_mask: pd.Series) -> SegmentClusterer:
        """Fit je Segment auf Train-Zeilen ohne ``{segment}_incomplete``.

        features : (site, date)-indizierte Segment-Feature-Matrix.
        train_mask : bool-Serie (gleicher Index), True = Trainingszeitraum.
        """
        for seg in self.segments:
            cols = self._cols(seg)
            mask = train_mask & ~features[f"{seg}_incomplete"].astype(bool)
            sub = features.loc[mask, cols].dropna()
            if len(sub) < self.k_per_segment[seg]:
                raise ValueError(f"Segment '{seg}': zu wenige Train-Zeilen ({len(sub)}).")
            scaler = StandardScaler().fit(sub.to_numpy())
            xs = scaler.transform(sub.to_numpy())
            km = KMeans(n_clusters=self.k_per_segment[seg], n_init=10, random_state=self.seed).fit(
                xs
            )
            train_min_dist = km.transform(xs).min(axis=1)
            self.scalers_[seg] = scaler
            self.kmeans_[seg] = km
            self.thresholds_[seg] = float(np.percentile(train_min_dist, self.threshold_percentile))
        return self

    def _check_fitted(self) -> None:
        if not self.kmeans_:
            raise RuntimeError("SegmentClusterer ist nicht gefittet – erst fit() aufrufen.")

    def score(self, features: pd.DataFrame) -> pd.DataFrame:
        """Min-Distanz zum nächsten Zentrum je Segment (kontinuierlich), für alle Zeilen.

        Spalten ``{segment}_distance``; NaN, wo Feature-Werte fehlen.
        """
        self._check_fitted()
        out: dict[str, pd.Series] = {}
        for seg in self.segments:
            cols = self._cols(seg)
            sub = features[cols]
            valid = sub.notna().all(axis=1)
            dist = pd.Series(np.nan, index=features.index, dtype=float)
            if valid.any():
                xs = self.scalers_[seg].transform(sub.loc[valid].to_numpy())
                dist.loc[valid] = self.kmeans_[seg].transform(xs).min(axis=1)
            out[f"{seg}_distance"] = dist
        return pd.DataFrame(out, index=features.index)

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Bool je Segment: Distanz über der (Train-kalibrierten) Perzentil-Schwelle."""
        scores = self.score(features)
        return pd.DataFrame(
            {
                f"{seg}_anomaly": scores[f"{seg}_distance"] > self.thresholds_[seg]
                for seg in self.segments
            },
            index=features.index,
        )

    def save(self, path: str | Path) -> None:
        self._check_fitted()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> SegmentClusterer:
        return joblib.load(path)
