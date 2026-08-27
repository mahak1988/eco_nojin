"""Carbon credit certificate PDF (Persian RTL, free stack).

Same rendering stack as the MRV report: fpdf2 full TTF embedding +
arabic_reshaper + python-bidi. Every field comes from real Supabase rows
(project, credits, owner, standard) — no fabricated numbers.
"""

import os
from typing import Any, Dict

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def fa(text: str) -> str:
        return get_display(arabic_reshaper.reshape(str(text)))

    _RTL_OK = True
except Exception:  # pragma: no cover
    def fa(text: str) -> str:
        return str(text)

    _RTL_OK = False


def _find_font() -> str:
    import glob

    candidates = [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        *glob.glob(r"C:\Windows\Fonts\vazir*.ttf"),
        *glob.glob(r"C:\Windows\Fonts\iran*.ttf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return r"C:\Windows\Fonts\arial.ttf"


def build_certificate_pdf(data: Dict[str, Any]) -> bytes:
    """Render a carbon-credit certificate as PDF bytes (one A4 landscape page)."""
    from fpdf import FPDF

    proj = data.get("project", {})
    credit = data.get("credit", {})
    owner = data.get("owner", {})
    meta = data.get("meta", {})

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_margins(20, 18, 20)

    font = _find_font()
    pdf.add_font("Persian", "", font)
    bold = font.replace("tahoma.ttf", "tahomabd.ttf").replace("segoeui.ttf", "segoeuib.ttf")
    if not os.path.exists(bold):
        bold = font
    pdf.add_font("Persian", "B", bold)

    w = pdf.w - 40

    def line(y: float, color: tuple = (15, 118, 110)) -> None:
        pdf.set_draw_color(*color)
        pdf.set_line_width(0.7)
        pdf.line(20, y, 20 + w, y)

    # header
    pdf.set_text_color(15, 118, 110)
    pdf.set_font("Persian", "B", 24)
    pdf.cell(0, 12, fa("گواهی اعتبار کربن — اکو نوژین"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_text_color(90, 90, 90)
    pdf.set_font("Persian", "", 10)
    pdf.cell(0, 7, fa("سند دیجیتال راستی‌آزمایی‌شده — قابل استعلام با کد اعتبارسنجی"), new_x="LMARGIN", new_y="NEXT", align="C")
    line(pdf.get_y() + 2)

    # credit code
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Persian", "B", 12)
    code = str(credit.get("id", ""))[:8].upper()
    pdf.cell(0, 9, fa(f"کد اعتبارسنجی: {code}"), new_x="LMARGIN", new_y="NEXT", align="C")

    # body
    pdf.ln(2)
    pdf.set_font("Persian", "", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 8, fa(f"این گواهی تأیید می‌کند که پروژه «{proj.get('name', '—')}» به مساحت "
                           f"{proj.get('area_ha', '—')} هکتار (نوع: {proj.get('project_type', '—')}) در چارچوب "
                           f"پلتفرم اکو نوژین راستی‌آزمایی شده است."), align="C")
    pdf.ln(2)
    pdf.set_text_color(15, 118, 110)
    pdf.set_font("Persian", "B", 17)
    pdf.cell(0, 12, fa(f"{credit.get('amount', '—')} تن معادل CO₂ (tCO2e)"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Persian", "", 12)
    pdf.multi_cell(0, 8, fa(f"مالک: {owner.get('display_name') or owner.get('email', '—')} — "
                           f"شناسه پروژه: {str(proj.get('id', ''))[:8]} — تاریخ صدور: {credit.get('issued_at', '—')}"), align="C")

    # standard
    pdf.ln(3)
    pdf.set_font("Persian", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 7, fa(f"مرجع: {meta.get('standard', 'IPCC 2019 Refinement')} — {meta.get('standard_link', '')}"), align="C")

    line(pdf.h - 42)
    pdf.set_y(pdf.h - 38)
    pdf.set_font("Persian", "", 9)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(0, 5, fa("این سند با ابزار رایگان و داده‌های واقعی پلتفرم تولید شده است و جایگزین گواهی‌های رسمی نهادهای اعطاکننده نیست."), align="C")
    return bytes(pdf.output())
