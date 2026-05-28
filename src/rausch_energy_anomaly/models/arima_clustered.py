"""ARIMA pro Peer-Gruppe auf der STL-saison-bereinigten Reihe (Trend + Remainder).

Hauptmethode A im Methodenvergleich. Vorgehen:

- **Saison via STL**, nicht via ``s`` in SARIMAX (s=96 wäre bei 15-min zu langsam):
  Eingang ist ``stl_deseasonalized`` (= Trend + Remainder) aus
  :func:`rausch_energy_anomaly.features.stl_decompose`. Auf dem reinen Remainder wäre
  ARIMA nahezu redundant zum Z-Score (Remainder ≈ weißes Rauschen); auf Trend+Remainder
  erfasst ARIMA echte Restdynamik/Trend (vgl. methodology.md).
- **Eine Ordnung je Peer-Gruppe** (k=3 → 3 Ordnungen), bestimmt via ``pmdarima.auto_arima``
  (Fallback: AIC-Grid mit statsmodels). Pro **Site** wird mit dieser Ordnung ein SARIMAX
  gefittet (site-spezifische Parameter, geteilte Ordnung).
- **Score** = standardisierte 1-Schritt-Innovation. **Kein Look-ahead**: die Vorhersage
  bei ``t`` nutzt nur Daten ``< t`` (``get_prediction(dynamic=False)``); werden Parameter
  auf einem Train-Slice gefittet, extendiert ``append(refit=False)`` mit **festen**
  Parametern, sodass spätere Werte die Scores davor nicht beeinflussen.
"""

from __future__ import annotations

import itertools
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

logger = logging.getLogger(__name__)

try:  # pmdarima ist primär; bei Problemen greift der AIC-Grid-Fallback
    import pmdarima as _pm

    _HAS_PMDARIMA = True
except Exception:  # pragma: no cover - Umgebungsabhängig
    _HAS_PMDARIMA = False


class ArimaClusteredDetector:
    """ARIMA-Anomalie-Detektor mit geteilter Ordnung je Peer-Gruppe.

    Parameters
    ----------
    max_p, max_q, max_d : Suchraum-Grenzen der Ordnung.
    z_threshold : Schwelle auf |standardisierte Innovation| für ``predict``.
    use_pmdarima : ``auto_arima`` nutzen (sonst direkt AIC-Grid).
    seed : Reproduzierbarkeit.
    """

    def __init__(
        self,
        max_p: int = 3,
        max_q: int = 3,
        max_d: int = 2,
        z_threshold: float = 3.0,
        use_pmdarima: bool = True,
        seed: int = 42,
        min_train: int = 100,
    ) -> None:
        self.max_p = max_p
        self.max_q = max_q
        self.max_d = max_d
        self._min_train = min_train
        self.z_threshold = z_threshold
        self.use_pmdarima = use_pmdarima
        self.seed = seed
        self.orders_: dict[str, tuple[int, int, int]] = {}

    # -- Ordnungssuche ----------------------------------------------------- #
    def _aic_grid(self, y: pd.Series) -> tuple[int, int, int]:
        best_order, best_aic = None, np.inf
        for p, d, q in itertools.product(
            range(self.max_p + 1), range(self.max_d + 1), range(self.max_q + 1)
        ):
            if p == 0 and q == 0:
                continue
            try:
                res = SARIMAX(
                    y, order=(p, d, q), enforce_stationarity=False, enforce_invertibility=False
                ).fit(disp=False)
            except Exception:  # noqa: BLE001
                continue
            if np.isfinite(res.aic) and res.aic < best_aic:
                best_order, best_aic = (p, d, q), res.aic
        if best_order is None:
            raise RuntimeError("Keine ARIMA-Ordnung konnte gefittet werden.")
        return best_order

    def _select_order(self, y: pd.Series) -> tuple[int, int, int]:
        if self.use_pmdarima and _HAS_PMDARIMA:
            try:
                model = _pm.auto_arima(
                    y,
                    seasonal=False,
                    max_p=self.max_p,
                    max_q=self.max_q,
                    max_d=self.max_d,
                    suppress_warnings=True,
                    error_action="ignore",
                )
                return tuple(model.order)
            except Exception as exc:  # noqa: BLE001
                logger.warning("auto_arima fehlgeschlagen (%s) -> AIC-Grid-Fallback.", exc)
        return self._aic_grid(y)

    # -- sklearn-style API ------------------------------------------------- #
    def fit(self, repr_series_by_group: dict[str, pd.Series]) -> ArimaClusteredDetector:
        """Bestimmt je Peer-Gruppe **eine** ARIMA-Ordnung auf deren Repräsentativreihe."""
        for group, series in repr_series_by_group.items():
            y = pd.to_numeric(series, errors="coerce").dropna().astype(float)
            self.orders_[group] = self._select_order(y)
            logger.info("Peer-Gruppe %s: ARIMA-Ordnung %s", group, self.orders_[group])
        return self

    def _check_fitted(self) -> None:
        if not self.orders_:
            raise RuntimeError("ArimaClusteredDetector ist nicht gefittet – erst fit() aufrufen.")

    def score(
        self,
        series: pd.Series,
        group: str,
        fit_end=None,
        exog: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """1-Schritt-Innovationen + standardisierter Score für eine Site.

        Mit ``fit_end`` werden die Parameter nur auf ``series[:fit_end]`` geschätzt und
        der Rest per ``append(refit=False)`` mit festen Parametern fortgeschrieben
        (kein Look-ahead, kein Test-Leakage). Spalten: ``forecast``, ``resid``,
        ``se``, ``zscore``.
        """
        self._check_fitted()
        order = self.orders_[group]
        y = pd.to_numeric(series, errors="coerce").astype(float)

        def _exog(idx: pd.Index) -> pd.DataFrame | None:
            return None if exog is None else exog.loc[idx]

        if fit_end is not None:
            # tz-robust: naiven date/Timestamp an die (ggf. tz-aware) Reihe angleichen
            fit_end = pd.Timestamp(fit_end)
            if getattr(y.index, "tz", None) is not None and fit_end.tz is None:
                fit_end = fit_end.tz_localize(y.index.tz)
            y_tr = y.loc[:fit_end]
            if len(y_tr) < self._min_train:
                # Site beginnt (fast) komplett nach fit_end -> kein Train-Slice verfügbar.
                # Fallback: auf der vollen Site-Reihe fitten (In-Sample-1-Schritt, kein Split).
                logger.warning(
                    "Zu wenig Train vor fit_end (%d Punkte) -> Fit auf voller Site-Reihe.",
                    len(y_tr),
                )
                fit_end = None  # in den else-Zweig unten fallen
        if fit_end is not None:
            y_te = y.loc[y.index > fit_end]
            res = SARIMAX(
                y_tr,
                order=order,
                exog=_exog(y_tr.index),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
            pred_tr = res.get_prediction(dynamic=False)
            mean, se = pred_tr.predicted_mean, pred_tr.se_mean
            if len(y_te):
                res2 = res.append(y_te, exog=_exog(y_te.index), refit=False)
                pred_te = res2.get_prediction(start=len(y_tr), dynamic=False)
                mean = pd.concat([mean, pred_te.predicted_mean])
                se = pd.concat([se, pred_te.se_mean])
        else:
            res = SARIMAX(
                y,
                order=order,
                exog=_exog(y.index),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
            pred = res.get_prediction(dynamic=False)
            mean, se = pred.predicted_mean, pred.se_mean

        resid = y - mean
        zscore = resid / se.replace(0, np.nan)
        return pd.DataFrame({"forecast": mean, "resid": resid, "se": se, "zscore": zscore})

    def predict(self, series: pd.Series, group: str, fit_end=None, exog=None) -> pd.Series:
        """1 = Anomalie (|standardisierte Innovation| > z_threshold)."""
        z = self.score(series, group, fit_end=fit_end, exog=exog)["zscore"]
        return (z.abs() > self.z_threshold).astype(int)

    def save(self, path: str | Path) -> None:
        self._check_fitted()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> ArimaClusteredDetector:
        return joblib.load(path)
