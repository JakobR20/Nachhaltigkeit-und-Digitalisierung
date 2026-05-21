"""Konvertiert Markdown-Dokumente nach PDF (reines Python, keine System-Libs).

markdown -> HTML -> fpdf2.write_html, mit eingebettetem Arial Unicode (deckt
Umlaute, €, →, ≈, −, ×, … ab). Aufruf:

    python docs/_md2pdf.py docs/konzept/methodenwahl_defense.md
    python docs/_md2pdf.py <in.md> [out.pdf]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import markdown
from fpdf import FPDF

FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
HEADING_SIZES = {"h1": 18, "h2": 13, "h3": 11, "h4": 10}


def _sanitize(html: str) -> str:
    """fpdf2-kompatibel machen: fpdf2 erlaubt keinen verschachtelten Markup in
    Tabellenzellen → Inline-Tags (strong/em/code) in allen <td>/<th> entfernen.
    Fließtext außerhalb von Tabellen bleibt unverändert (inkl. Fettung)."""
    html = re.sub(r"</?code>", "", html)

    def strip_inner(m: re.Match) -> str:
        return m.group(1) + re.sub(r"<[^>]+>", "", m.group(2)) + m.group(3)

    return re.sub(
        r"(<(?:td|th)(?:\s[^>]*)?>)(.*?)(</(?:td|th)>)",
        strip_inner,
        html,
        flags=re.DOTALL,
    )


def convert(md_path: Path, pdf_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    html = _sanitize(html)

    pdf = FPDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(auto=True, margin=16)
    for style in ("", "B", "I", "BI"):
        pdf.add_font("ArialUni", style, FONT)
    pdf.add_page()
    pdf.set_font("ArialUni", size=10)
    pdf.write_html(
        html,
        heading_sizes=HEADING_SIZES,
        table_line_separators=True,
    )
    pdf.output(str(pdf_path))
    print("geschrieben:", pdf_path, f"({pdf.pages_count} Seiten)")


def main(argv: list[str]) -> None:
    inp = Path(argv[0])
    out = Path(argv[1]) if len(argv) > 1 else inp.with_suffix(".pdf")
    convert(inp, out)


if __name__ == "__main__":
    main(sys.argv[1:])
