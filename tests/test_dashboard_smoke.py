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


def test_all_pages_render_without_exception():
    at = AppTest.from_file(APP, default_timeout=150).run()
    for page in ("Übersicht", "Methodenvergleich", "Standort-Detail", "Anomalie-Detail"):
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, f"page {page} raised: {at.exception}"


def test_site_detail_slider_rerun():
    at = AppTest.from_file(APP, default_timeout=150).run()
    at.sidebar.radio[0].set_value("Standort-Detail").run()
    assert len(at.slider) == 3  # z-score, ARIMA sigma, AE percentile
    at.slider[0].set_value(5.0).run()  # re-threshold must not crash
    assert not at.exception
