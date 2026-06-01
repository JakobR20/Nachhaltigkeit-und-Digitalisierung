"""Custom CSS and small UI helpers for the dashboard.

Scope is intentionally small (no animations, no custom fonts, no theme toggle):
- a header block for the page title,
- visually distinct cards for the LLM recommendation vs. the context block,
- coloured severity badges.
Colours are read from config/dashboard.yaml so they stay in sync with the plots.
"""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
.block-container { padding-top: 2.2rem; padding-bottom: 2.5rem; max-width: 1400px; }
.dash-header {
    border-left: 5px solid var(--rausch-red, #d62728);
    padding: 0.2rem 0 0.2rem 0.9rem; margin-bottom: 1.1rem;
}
.dash-header h2 { margin: 0; font-size: 1.5rem; }
.dash-header .sub { color: #6b7280; font-size: 0.9rem; }
.dash-card {
    background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
    padding: 1rem 1.2rem; margin-bottom: 0.8rem;
}
.dash-card.llm { border-left: 5px solid #d62728; }
.dash-card.context { border-left: 5px solid #6b7280; background: #f9fafb; }
.dash-card h4 { margin: 0 0 0.5rem 0; }
.sev-badge {
    display: inline-block; padding: 0.12rem 0.6rem; border-radius: 999px;
    color: #fff; font-size: 0.8rem; font-weight: 600; vertical-align: middle;
}
.section-gap { margin-top: 1.4rem; }
</style>
"""

_SEVERITY_HEX = {"hoch": "#d62728", "mittel": "#ff7f0e", "niedrig": "#2ca02c"}


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="dash-header"><h2>{title}</h2>{sub}</div>',
                unsafe_allow_html=True)


def severity_badge(sev: str) -> str:
    """Inline HTML badge for a severity level (use inside st.markdown unsafe_html)."""
    hex_ = _SEVERITY_HEX.get(sev, "#6b7280")
    return f'<span class="sev-badge" style="background:{hex_}">{sev}</span>'
