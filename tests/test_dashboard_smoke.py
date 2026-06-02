"""Headless render smoke-tests for the dashboard (Streamlit AppTest).

No browser needed: AppTest runs the script and inspects the element tree. Covers
the cost-first main pages (list + detail with its cost-calc variants) and the
research tab (the legacy 4 pages). Views are driven via session_state to avoid the
AppTest selectbox-rerun quirk; navigation buttons are covered separately.
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "dashboard.py")


def _run(view: str | None = None, detail_nr: str | None = None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=120)
    if view:
        at.session_state["view"] = view
    if detail_nr:
        at.session_state["detail_nr"] = detail_nr
    return at.run()


def _md(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown)


def test_list_renders_with_brand_and_cards():
    at = _run()
    assert not at.exception
    assert "THWS" in _md(at)
    assert len([b for b in at.button if b.label.startswith("Details")]) == 66
    assert len(at.selectbox) == 4  # four filters


def test_detail_renders_all_blocks():
    at = _run(view="detail", detail_nr="21")  # highest cost
    assert not at.exception
    md = _md(at)
    for block in ("Kostenanalyse", "KI-Analyse", "Rahmenbedingungen", "Vermutete Ursache"):
        assert block in md, f"missing block: {block}"
    assert len(at.get("plotly_chart")) == 1


def test_detail_negative_price_block():
    at = _run(view="detail", detail_nr="58")  # negative spot price
    assert not at.exception
    md = _md(at)
    assert "negativ" in md and "0,00 €" in md


def test_detail_underconsumption_block():
    at = _run(view="detail", detail_nr="4")  # diff_kw < 0
    assert not at.exception
    md = _md(at)
    assert "Minderverbrauch" in md


def test_card_click_navigates_to_detail():
    at = _run()
    [b for b in at.button if b.label.startswith("Details")][0].click().run()
    assert not at.exception
    assert at.session_state["view"] == "detail"


def test_research_tab_exposes_legacy_pages():
    at = _run(view="research")
    assert not at.exception
    assert at.sidebar.radio[0].options == [
        "Übersicht", "Methodenvergleich", "Standort-Detail", "Anomalie-Detail",
    ]
