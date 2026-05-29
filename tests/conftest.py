"""Pytest-Konfiguration: TensorFlow-Logs stummschalten, BEVOR TF importiert wird.

TFs stderr-Flut kann eine stderr-Pipe (z. B. ``pytest ... 2>&1 | grep``) zum Deadlock
bringen. ``TF_CPP_MIN_LOG_LEVEL=3`` muss vor dem ersten ``import tensorflow`` gesetzt sein
– deshalb hier in conftest.py (wird vor der Test-Sammlung geladen).
"""

import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
# os.environ.setdefault("OMP_NUM_THREADS", "1")  # gegen den TF-Threadpool-Deadlock auf macOS
