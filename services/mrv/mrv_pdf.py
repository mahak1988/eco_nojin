"""MRV PDF report generator — گزارش PDF بودجه کربن (فارسی RTL، رایگان).

Stack: fpdf2 (MIT, Unicode TTF embedding — full font, no subsetting issues)
+ arabic-reshaper (MIT) + python-bidi (LGPL) for RTL Persian.
Every figure comes from the real chain (RothC-26.3 / ERA5 / SoilGrids)
plus optional KoboToolbox field data — no fabricated numbers.
"""

import os
from typing import Any, Dict

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def fa(text: str) -> str:
        return get_display(arabic_reshaper.reshape(str(text)))

    _RTL_OK = True
except Exception:  # pragma: no cover - fallback keeps PDF generation alive
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


def build_mrv_pdf(data: Dict[str, Any]) -> bytes:
    """Render the MRV carbon-budget report as PDF bytes (single page)."""
    from fpdf import FPDF

    c = data.get("carbon", {})
    loc = data.get("location", {})
    kobo = data.get("kobo", {}) or {}
    periods = c.get("periods") or []
    subs = kobo.get("submissions") or []

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 16, 18)

    font = _find_font()
    pdf.add_font("Persian", "", font)
    bold = font.replace("tahoma.ttf", "tahomabd.ttf").replace("segoeui.ttf", "segoeuib.ttf")
    if os.path.exists(bold):
        pdf.add_font("Persian", "B", bold)
    else:
        bold = font
        pdf.add_font("Persian", "B", bold)

    def heading(txt: str, size: int = 17, color: tuple = (15, 118, 110)) -> None:
        pdf.set_text_color(*color)
        pdf.set_font("Persian", "B", size)
        pdf.cell(0, 10, fa(txt), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(1)

    def sub(txt: str) -> None:
        pdf.set_text_color(15, 118, 110)
        pdf.set_font("Persian", "B", 12)
        pdf.cell(0, 8, fa(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def para(txt: str, size: float = 9.5, color: tuple = (30, 41, 59)) -> None:
        pdf.set_text_color(*color)
        pdf.set_font("Persian", "", size)
        pdf.multi_cell(0, 6, fa(txt), align="R")
        pdf.ln(1)

    # Header
    pdf.set_fill_color(15, 118, 110)
    pdf.rect(0, 0, 210, 26, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Persian", "B", 18)
    pdf.set_y(7)
    pdf.cell(0, 10, fa("گزارش بودجه کربن خاک (MRV) — اکو نوژین"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Persian", "", 9)
    pdf.cell(
        0, 7,
        fa(f"موقعیت: {loc.get('lat', '—')}°N, {loc.get('lon', '—')}°E  ·  متد: {c.get('methodology', '—')}"),
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.set_y(32)

    # Key results table
    sub("نتایج اصلی")
    delta = c.get("delta_co2e_total")
    delta_txt = f"{delta:+,.1f} tCO2e" if isinstance(delta, (int, float)) else "—"
    rows = [
        ("شاخص", "مقدار"),
        ("تغییر کل", delta_txt),
        ("به ازای هکتار (tCO2e/ha)", f"{c.get('delta_co2e_ha', '—')}"),
        ("SOC اولیه (t C/ha)", f"{c.get('soc_initial_t_ha', '—')}"),
        ("SOC نهایی (t C/ha)", f"{c.get('soc_final_t_ha', '—')}"),
        ("تغییر سالانه SOC", f"{c.get('delta_soc_t_ha_yr', '—')} t C/ha"),
        ("مساحت", f"{c.get('area_ha', '—')} ha"),
        ("حالت داده", f"{c.get('data_mode', '—')}"),
        ("ضریب ماندگاری", f"{c.get('permanence_factor', '—')}"),
        ("گواهی‌پذیر (tCO2e)", f"{c.get('certified_delta_co2e_total', '—')}"),
    ]
    pdf.set_font("Persian", "B", 9.5)
    pdf.set_fill_color(240, 253, 250)
    pdf.set_draw_color(203, 213, 225)
    for i, (k, v) in enumerate(rows):
        if i == 0:
            pdf.set_fill_color(15, 118, 110)
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_fill_color(255, 255, 255 if i % 2 else 240, )
            pdf.set_text_color(30, 41, 59)
        pdf.set_font("Persian", "B" if i == 0 else "", 9.5)
        pdf.cell(90, 7, fa(k), border=1, fill=True, align="R")
        pdf.cell(84, 7, fa(v), border=1, fill=True, align="C")
        pdf.ln()

    pdf.ln(3)

    # Multi-period trend
    if periods:
        sub("روند چنددوره‌ای (t0 → t5)")
        pdf.set_font("Persian", "B", 9.5)
        pdf.set_fill_color(15, 118, 110)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(58, 7, fa("سال"), border=1, fill=True, align="C")
        pdf.cell(58, 7, fa("SOC (t C/ha)"), border=1, fill=True, align="C")
        pdf.cell(58, 7, fa("تغییر (tCO2e/ha)"), border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(30, 41, 59)
        for idx, p in enumerate(periods):
            pdf.set_fill_color(255, 255, 255 if idx % 2 else 240)
            pdf.set_font("Persian", "", 9.5)
            pdf.cell(58, 7, fa(str(p.get("year", "—"))), border=1, fill=True, align="C")
            pdf.cell(58, 7, fa(f"{p.get('soc_t_ha', '—')}"), border=1, fill=True, align="C")
            pdf.cell(58, 7, fa(f"{p.get('delta_tco2e_ha', '—')}"), border=1, fill=True, align="C")
            pdf.ln()
        pdf.ln(3)

    # Field data
    sub("داده میدانی (KoboToolbox)")
    if subs:
        pdf.set_font("Persian", "B", 9.5)
        pdf.set_fill_color(15, 118, 110)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(58, 7, fa("زمان"), border=1, fill=True, align="C")
        pdf.cell(58, 7, fa("SOC (t C/ha)"), border=1, fill=True, align="C")
        pdf.cell(58, 7, fa("مختصات"), border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(30, 41, 59)
        for idx, sub in enumerate(subs[:20]):
            pdf.set_fill_color(255, 255, 255 if idx % 2 else 240)
            pdf.set_font("Persian", "", 9.5)
            pdf.cell(58, 7, fa(str(sub.get("time", "—"))[:10]), border=1, fill=True, align="C")
            pdf.cell(58, 7, fa(f"{sub.get('soc_t_ha', '—')}"), border=1, fill=True, align="C")
            pdf.cell(58, 7, fa(f"{sub.get('lat', '—')}, {sub.get('lon', '—')}"), border=1, fill=True, align="C")
            pdf.ln()
    else:
        para(f"وضعیت: {kobo.get('status', '—')} — {kobo.get('hint', 'نمونه‌ای ثبت نشده')}")

    pdf.ln(3)
    para(
        "توضیح: برآورد مدل بر پایه زنجیره علمی واقعی (RothC-26.3 با اقلیم ERA5 و خاک SoilGrids) است. "
        "این گزارش گواهی رسمی Verra/Gold Standard نیست؛ ثبت در رجیستری نیازمند مستندات کامل متدولوژی است.",
        size=8, color=(100, 116, 139),
    )

    return bytes(pdf.output())
