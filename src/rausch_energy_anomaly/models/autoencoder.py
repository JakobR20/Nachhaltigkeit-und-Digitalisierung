"""Autoencoder-Anomalieerkennung auf dem rohen 24h-Lastgang (pro Kategorie).

Hauptmethode B im Methodenvergleich. Designentscheidungen (vgl. methodology.md):

- **Eingang = roher Lastgang** (nicht STL-Residual): der AE lernt die Saisonalität selbst
  und misst Abweichungen vom typischen Tagesmuster (Form **und** site-internes Niveau).
- **Normierung pro Site** (StandardScaler, auf Train gefittet): entfernt die Zwischen-Site-
  Magnitude (sonst dominiert die größte Site das eine Kategorie-Modell), erhält aber das
  site-interne Niveau → durchgehend erhöhte Tage werden erkannt.
- **Score pro 15-min-Punkt** = Rekonstruktionsfehler je Slot (`granularity="point"`,
  passt zum gemeinsamen Format); `flag` = Fehler über Perzentil-Schwelle (Train-Fehler).
- **Ein Modell je Kategorie** über alle Sites; `variant ∈ {dense, lstm}` in einer Klasse
  (v4 §4 nennt zwei Dateien – bewusst zusammengefasst, v4 ist Plan, kein Vertrag).

Nur volle 96-Slot-Tage gehen in die Fenster (DST-/Teiltage werden übersprungen).
Determinismus: Seeds gesetzt; bei TensorFlow ist exakte Bit-Reproduzierbarkeit jedoch
nicht garantiert.
"""

from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# TF-Logs stummschalten, BEVOR TensorFlow importiert wird. Wichtig auch fürs
# Produktiv-Scoring: TFs stderr-Flut deadlockt sonst eine stderr-Pipe (siehe der
# grep-Pipe-Hang). Konsumenten (scoring.py-Driver) erben diese Einstellung.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import tensorflow as tf  # noqa: E402

tf.get_logger().setLevel("ERROR")

# macOS: TFs Multi-Thread-Threadpool deadlockt intermittierend in model.fit (0 % CPU-Hang,
# reproduzierbar nur unter Last). Single-Thread erzwingen – die Tagesfenster (96 Werte) sind
# winzig, Tempo ist unkritisch, Zuverlässigkeit zählt. Vor dem ersten TF-Op setzen.
try:  # pragma: no cover - umgebungsabhängig
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
except RuntimeError:
    pass

_SLOTS = 96  # 24 h auf 15-min-Basis
# TensorFlow/Keras 3 läuft mit float64-Eingaben in einen Hang -> immer float32.
_DTYPE = "float32"


def _day_windows(series: pd.Series) -> pd.DataFrame:
    """Pivotiert eine 15-min-Reihe auf (date × 96 Slots); nur volle Tage."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    ts = s.index
    frame = pd.DataFrame(
        {"date": ts.normalize(), "slot": ts.hour * 4 + ts.minute // 15, "v": s.to_numpy()}
    )
    piv = frame.pivot_table(index="date", columns="slot", values="v")
    return piv.reindex(columns=range(_SLOTS)).dropna()


class AutoencoderDetector:
    """Dense- oder LSTM-Autoencoder je Kategorie auf rohen Tagesfenstern.

    Parameters
    ----------
    variant : "dense" | "lstm".
    latent_dim, hidden : Engpass-/Hidden-Größe.
    epochs, batch_size, validation_fraction : Training.
    threshold_percentile : Perzentil der Train-Rekonstruktionsfehler als Anomalie-Schwelle.
    seed : Reproduzierbarkeit.
    """

    def __init__(
        self,
        variant: str = "dense",
        latent_dim: int = 8,
        hidden: int = 32,
        epochs: int = 30,
        batch_size: int = 64,
        validation_fraction: float = 0.1,
        threshold_percentile: float = 99.0,
        seed: int = 42,
    ) -> None:
        if variant not in ("dense", "lstm"):
            raise ValueError(f"variant muss 'dense' oder 'lstm' sein, nicht {variant!r}")
        self.variant = variant
        self.latent_dim = latent_dim
        self.hidden = hidden
        self.epochs = epochs
        self.batch_size = batch_size
        self.validation_fraction = validation_fraction
        self.threshold_percentile = threshold_percentile
        self.seed = seed
        self.scalers_: dict[str, StandardScaler] = {}
        self.model_: tf.keras.Model | None = None
        self.threshold_: float | None = None

    # -- Modellaufbau ------------------------------------------------------ #
    def _build(self) -> tf.keras.Model:
        from tensorflow.keras import Input, Model, layers

        if self.variant == "dense":
            inp = Input(shape=(_SLOTS,))
            x = layers.Dense(self.hidden, activation="relu")(inp)
            z = layers.Dense(self.latent_dim, activation="relu")(x)
            x = layers.Dense(self.hidden, activation="relu")(z)
            out = layers.Dense(_SLOTS, activation="linear")(x)
        else:  # lstm
            inp = Input(shape=(_SLOTS, 1))
            z = layers.LSTM(self.hidden)(inp)
            z = layers.Dense(self.latent_dim, activation="relu")(z)
            x = layers.RepeatVector(_SLOTS)(z)
            x = layers.LSTM(self.hidden, return_sequences=True)(x)
            out = layers.TimeDistributed(layers.Dense(1))(x)
        model = Model(inp, out)
        model.compile(optimizer="adam", loss="mse")
        return model

    def _shape(self, x: np.ndarray) -> np.ndarray:
        return x.reshape(x.shape[0], _SLOTS, 1) if self.variant == "lstm" else x

    # -- sklearn-style API ------------------------------------------------- #
    def fit(self, series_by_site: dict[str, pd.Series], fit_end=None) -> AutoencoderDetector:
        """Trainiert ein Modell über alle Sites der Kategorie (Train-Slice bis fit_end)."""
        tf.keras.utils.set_random_seed(self.seed)
        parts = []
        for site, series in series_by_site.items():
            train = series.loc[:fit_end] if fit_end is not None else series
            scaler = StandardScaler().fit(train.to_numpy(dtype=float).reshape(-1, 1))
            self.scalers_[site] = scaler
            win = _day_windows(train)
            if len(win):
                x = scaler.transform(win.to_numpy().reshape(-1, 1)).reshape(win.shape)
                parts.append(x.astype(_DTYPE))
        if not parts:
            raise ValueError("Keine vollständigen Trainings-Tagesfenster vorhanden.")
        x_train = np.concatenate(parts, axis=0)

        self.model_ = self._build()
        # Validierungs-Split (+EarlyStopping) nur bei genug Fenstern, sonst degeneriert.
        val = self.validation_fraction if len(x_train) >= 20 else 0.0
        callbacks = (
            [
                tf.keras.callbacks.EarlyStopping(
                    monitor="val_loss", patience=5, restore_best_weights=True
                )
            ]
            if val > 0
            else []
        )
        self.model_.fit(
            self._shape(x_train),
            self._shape(x_train),
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_split=val,
            callbacks=callbacks,
            verbose=0,
        )
        recon = self.model_.predict(self._shape(x_train), verbose=0).reshape(x_train.shape)
        err = (x_train - recon) ** 2
        self.threshold_ = float(np.percentile(err, self.threshold_percentile))
        return self

    def _check_fitted(self) -> None:
        if self.model_ is None:
            raise RuntimeError("AutoencoderDetector ist nicht gefittet – erst fit() aufrufen.")

    def score(self, series: pd.Series, site: str) -> pd.Series:
        """Rekonstruktionsfehler je 15-min-Punkt (nur volle Tage). Index = timestamp."""
        self._check_fitted()
        scaler = self.scalers_.get(site) or StandardScaler().fit(
            pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=float).reshape(-1, 1)
        )
        win = _day_windows(series)
        if not len(win):
            return pd.Series(dtype=float, name="error")
        x = scaler.transform(win.to_numpy().reshape(-1, 1)).reshape(win.shape).astype(_DTYPE)
        recon = self.model_.predict(self._shape(x), verbose=0).reshape(x.shape)
        err = (x - recon) ** 2
        # (date × 96) zurück auf Zeitstempel abbilden
        idx = [d + pd.Timedelta(minutes=15 * slot) for d in win.index for slot in range(_SLOTS)]
        return pd.Series(err.reshape(-1), index=pd.DatetimeIndex(idx), name="error").sort_index()

    def predict(self, series: pd.Series, site: str) -> pd.Series:
        """1 = Anomalie (Rekonstruktionsfehler über Train-Schwelle)."""
        err = self.score(series, site)
        return (err > self.threshold_).astype(int)

    # -- Persistenz -------------------------------------------------------- #
    def save(self, directory: str | Path) -> None:
        self._check_fitted()
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.model_.save(directory / "model.keras")
        meta = {
            "variant": self.variant,
            "scalers_": self.scalers_,
            "threshold_": self.threshold_,
            "latent_dim": self.latent_dim,
            "hidden": self.hidden,
            "seed": self.seed,
        }
        joblib.dump(meta, directory / "meta.joblib")

    @staticmethod
    def load(directory: str | Path) -> AutoencoderDetector:
        directory = Path(directory)
        meta = joblib.load(directory / "meta.joblib")
        det = AutoencoderDetector(
            variant=meta["variant"],
            latent_dim=meta["latent_dim"],
            hidden=meta["hidden"],
            seed=meta["seed"],
        )
        det.scalers_ = meta["scalers_"]
        det.threshold_ = meta["threshold_"]
        det.model_ = tf.keras.models.load_model(directory / "model.keras")
        return det
