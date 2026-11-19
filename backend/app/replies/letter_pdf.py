"""Render a reply as a DIN 5008 (Form B) business letter PDF.

Pure Python (fpdf2), so it runs anywhere without system libraries.
Positions in mm follow DIN 5008 Form B: address field 45 mm from the top,
left margin 25 mm, fold marks at 105 mm and 210 mm, hole mark at 148.5 mm.
"""

from __future__ import annotations

from datetime import date

from fpdf import FPDF

LEFT = 25
RIGHT = 20
WIDTH = 210 - LEFT - RIGHT

# Built-in PDF fonts only cover Latin-1; map the few characters we need.
_REPLACE = {"–": "-", "—": "-", "„": '"', "“": '"', "”": '"', "‚": "'", "‘": "'", "’": "'", "…": "...", "€": "EUR"}


def _latin1(text: str) -> str:
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


def render_letter_pdf(
    *,
    sender_name: str,
    sender_address: str,
    recipient_address: str,
    city: str,
    subject: str,
    body: str,
    letter_date: date | None = None,
) -> bytes:
    letter_date = letter_date or date.today()
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.set_margins(LEFT, 20, RIGHT)
    pdf.add_page()

    # Fold and hole marks
    pdf.set_draw_color(150, 150, 150)
    for y, length in ((105, 5), (148.5, 7), (210, 5)):
        pdf.line(3, y, 3 + length, y)

    # Sender block (top right)
    pdf.set_font("Helvetica", size=10)
    pdf.set_xy(125, 20)
    pdf.multi_cell(65, 4.5, _latin1(sender_name + "\n" + sender_address), align="L")

    # Return line + address field (Form B: 45 mm from top, 85 x 45 mm)
    pdf.set_font("Helvetica", size=7)
    pdf.set_xy(LEFT, 45)
    one_line = ", ".join([sender_name] + [line for line in sender_address.splitlines() if line.strip()])
    pdf.cell(85, 4, _latin1(one_line[:80]), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.set_xy(LEFT, 62.7)
    pdf.multi_cell(85, 5, _latin1(recipient_address), align="L")

    # Date (right aligned, level with the information block)
    pdf.set_xy(125, 97.4)
    pdf.cell(65, 5, _latin1(f"{city}, {letter_date.strftime('%d.%m.%Y')}"), align="R")

    # Subject: two blank lines below the address field, bold, no "Betreff:" label (DIN 5008)
    pdf.set_xy(LEFT, 103.46)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.multi_cell(WIDTH, 5.5, _latin1(subject))
    pdf.ln(6)

    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(WIDTH, 5.5, _latin1("Sehr geehrte Damen und Herren,"))
    pdf.ln(4)
    pdf.multi_cell(WIDTH, 5.5, _latin1(body))
    pdf.ln(6)
    pdf.multi_cell(WIDTH, 5.5, _latin1("Mit freundlichen Grüßen"))
    pdf.ln(16)  # space for the handwritten signature
    pdf.multi_cell(WIDTH, 5.5, _latin1(sender_name))

    return bytes(pdf.output())
