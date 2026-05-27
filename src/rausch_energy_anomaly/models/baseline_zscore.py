"""Globaler Z-Score-Detektor als Baseline-Anomalieerkennung.

Bewusst die einfachste, voll erklärbare Methode (3-Sigma-Regel) – der Maßstab,
gegen den die komplexeren Verfahren (ARIMA, Isolation Forest) antreten müssen.

sklearn-style API (fit/score/predict), arbeitet auf **einer** Zeitreihe. Die
Anwendung pro Zähler erfolgt aufrufseitig (groupby), weil die Standardisierung
per Definition verteilungsbezogen ist und die Residuenverteilung je Zähler
unterschiedlich ist.

Eingang ist typischerweise das STL-Residuum (`stl_resid`), nicht der Rohwert:
Saison und Trend sind dort bereits entfernt, der Z-Score misst also die
„Untypischkeit für diesen Zeitpunkt".
"""

from __future__ import annotations

import pandas as pd


class ZScoreDetector:
    """Globaler Z-Score über die volle Historie einer Reihe.

    Parameters
    ----------
    threshold : float
        Schwelle auf den Betrag des Z-Scores. 3.0 entspricht der 3-Sigma-Regel.
    """

    def __init__(self, threshold: float = 3.0) -> None:
        self.threshold = threshold
        self.mean_: float | None = None
        self.std_: float | None = None

    def fit(self, series: pd.Series) -> ZScoreDetector:
        s = pd.Series(series).dropna()
        if s.empty:
            raise ValueError("fit: Serie ist leer.")
        self.mean_ = float(s.mean())
        self.std_ = float(s.std(ddof=0))
        if self.std_ == 0:
            raise ValueError("fit: Standardabweichung ist 0 – konstante Reihe.")
        return self

    def _check_fitted(self) -> None:
        if self.mean_ is None or self.std_ is None:
            raise RuntimeError("Detector ist nicht gefittet – erst fit() aufrufen.")

    def score(self, series: pd.Series) -> pd.Series:
        """Z-Scores (vorzeichenbehaftet) als Serie mit identischem Index."""
        self._check_fitted()
        s = pd.Series(series)
        return (s - self.mean_) / self.std_

    def predict(self, series: pd.Series) -> pd.Series:
        """1 = Anomalie (|z| > threshold), 0 = normal."""
        z = self.score(series)
        return (z.abs() > self.threshold).astype(int)
