"""CSS and UI helpers for the dashboard.

Two layers:
- Apple-HIG layer (cost-first main pages): grouped background, system font,
  rounded white cards with subtle shadow, system accent/severity colours.
- legacy layer (research tab): header block, llm/context cards, severity badges —
  kept so the moved research pages still render as before.
"""

from __future__ import annotations

import streamlit as st

# --- Apple HIG palette ---
HIG_BG = "#F2F2F7"
HIG_CARD = "#FFFFFF"
HIG_ACCENT = "#007AFF"
HIG_TEXT = "#1C1C1E"
HIG_SECONDARY = "#8E8E93"
HIG_SEVERITY = {"hoch": "#FF3B30", "mittel": "#FF9500", "niedrig": "#34C759"}

_FONT = ("-apple-system, BlinkMacSystemFont, 'SF Pro Display', "
         "'Helvetica Neue', sans-serif")

_HIG_CSS = f"""
<style>
.stApp {{ background: {HIG_BG}; }}
html, body, [class*="css"] {{ font-family: {_FONT}; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1100px; }}

.hig-brand {{ font-size: 1.7rem; font-weight: 700; color: {HIG_TEXT}; line-height: 1.1; }}
.hig-brand-sub {{ font-size: 0.95rem; color: {HIG_SECONDARY}; margin-bottom: 0.2rem; }}
.hig-title {{ font-size: 1.15rem; font-weight: 600; color: {HIG_TEXT}; margin: 0.6rem 0 0.2rem; }}

.hig-card {{
    background: {HIG_CARD}; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s ease;
}}
.hig-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.10), 0 1px 3px rgba(0,0,0,0.06); }}

.hig-cost {{ font-size: 28px; font-weight: 700; color: {HIG_TEXT};
            font-feature-settings: 'tnum'; letter-spacing: -0.5px; }}
.hig-site {{ font-size: 17px; font-weight: 500; color: {HIG_TEXT}; }}
.hig-meta {{ font-size: 13px; color: {HIG_SECONDARY}; }}
.hig-cause {{ font-size: 14px; color: #3A3A3C; margin-top: 0.3rem; }}
.hig-link {{ color: {HIG_ACCENT}; font-weight: 500; font-size: 14px; text-decoration: none; }}

.hig-pill {{ display: inline-block; padding: 0.15rem 0.7rem; border-radius: 999px;
            color: #fff; font-size: 0.78rem; font-weight: 600; }}
.hig-calc {{ font-family: 'SF Mono', ui-monospace, monospace; font-size: 13.5px;
            color: {HIG_TEXT}; background: #FAFAFC; border-radius: 8px;
            padding: 14px 18px; white-space: pre-wrap; line-height: 1.6; }}
.hig-foot {{ color: {HIG_SECONDARY}; font-size: 13px; margin-top: 1rem; }}
</style>
"""

# --- legacy layer (research tab) ---
_LEGACY_CSS = """
<style>
.dash-header { border-left: 5px solid #d62728; padding: 0.2rem 0 0.2rem 0.9rem;
               margin-bottom: 1.1rem; }
.dash-header h2 { margin: 0; font-size: 1.5rem; }
.dash-header .sub { color: #6b7280; font-size: 0.9rem; }
.dash-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
             padding: 1rem 1.2rem; margin-bottom: 0.8rem; }
.dash-card.llm { border-left: 5px solid #d62728; }
.dash-card.context { border-left: 5px solid #6b7280; background: #f9fafb; }
.dash-card h4 { margin: 0 0 0.5rem 0; }
.sev-badge { display: inline-block; padding: 0.12rem 0.6rem; border-radius: 999px;
             color: #fff; font-size: 0.8rem; font-weight: 600; vertical-align: middle; }
</style>
"""

_LEGACY_SEVERITY = {"hoch": "#d62728", "mittel": "#ff7f0e", "niedrig": "#2ca02c"}


def inject_css() -> None:
    """Apple-HIG styling for the main cost-first pages."""
    st.markdown(_HIG_CSS, unsafe_allow_html=True)


def inject_legacy_css() -> None:
    """Legacy styling for the research tab pages."""
    st.markdown(_LEGACY_CSS, unsafe_allow_html=True)


def hig_pill(label: str, severity: str) -> str:
    """Apple system-colour severity pill (HTML)."""
    hex_ = HIG_SEVERITY.get(severity, HIG_SECONDARY)
    return f'<span class="hig-pill" style="background:{hex_}">{label}</span>'


def plotly_hig_layout() -> dict[str, object]:
    """Transparent, system-font Plotly layout matching the Apple look."""
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": _FONT, "color": HIG_TEXT, "size": 13},
        "xaxis": {"gridcolor": "#E5E5EA", "zerolinecolor": "#E5E5EA"},
        "yaxis": {"gridcolor": "#E5E5EA", "zerolinecolor": "#E5E5EA"},
        "margin": {"t": 10, "b": 10, "l": 10, "r": 10},
    }


def header(title: str, subtitle: str = "") -> None:
    """Legacy header block (research tab)."""
    sub = f'<div class="sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="dash-header"><h2>{title}</h2>{sub}</div>',
                unsafe_allow_html=True)


def severity_badge(sev: str) -> str:
    """Legacy inline severity badge (research tab)."""
    hex_ = _LEGACY_SEVERITY.get(sev, "#6b7280")
    return f'<span class="sev-badge" style="background:{hex_}">{sev}</span>'
