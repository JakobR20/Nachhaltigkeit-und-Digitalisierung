"""Headless render smoke-test for the dashboard pages (Streamlit AppTest).

No browser needed: AppTest runs the script and inspects the element tree. Verifies
each page renders without exception and produces its key elements. Screenshots are
captured separately/manually.
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "dashboard.py")


def test_overview_renders_without_exception():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    # site matrix + top-10 + method-kappa card = 3 dataframes, 1 severity chart
    assert len(at.dataframe) >= 3
    assert len(at.get("plotly_chart")) >= 1
    caps = " ".join(c.value for c in at.caption)
    assert "Standorte" in caps
