"""رسم نمودار برای شکل‌های اعلام‌شدهٔ کتابچه‌ها.

فارسی در matplotlib نیازمند دو گام است:
  ۱) پیوندن حروف با arabic_reshaper  (وگرنه حروف جدا می‌مانند)
  ۲) بازچینش دوجهته با python-bidi     (وگرنه ترتیب کلمات وارونه می‌شود)
بدون این دو، برچسب فارسی ناخواناست. هر دو بسته در محیط موجودند.

دادهٔ نمودارها از پروندهٔ figures_data.json خوانده می‌شود.
هر ردیف آن چنین است:

    {
      "id":      "۹.۱",
      "book":    "HP-17",
      "kind":    "line" | "bar" | "grouped_bar" | "stacked_bar" | "area" | "scatter",
      "title":   "عنوان کوتاه روی نمودار",
      "x_label": "سال",
      "y_label": "دلار بر هکتار",
      "x":       ["سال ۱", "سال ۲", ...],
      "series":  [{"name": "هزینه", "y": [126, 0, ...]}, ...],
      "conf":    "فرض طراحی · سطح اطمینان C",
      "source":  "جدول ۹.۱ سطر ۲۷۳۶"
    }

اجرا:
    python scripts/print/figures.py            # همه
    python scripts/print/figures.py --book HP-17
"""

from __future__ import annotations

import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import arabic_reshaper
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
DATA = os.path.join(HERE, "figures_data.json")

# رنگ‌های چاپ‌پسند: کم‌اشباع، برای چاپ سیاه‌وسفید هم تفکیک‌پذیر
PALETTE = ["#1d3f2e", "#8c5a2b", "#3f6b8c", "#7a3b52", "#5c6b2f", "#4a4a4a"]
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def fa(s: str) -> str:
    """پیوندن + بازچینش متن فارسی برای matplotlib."""
    if s is None:
        return ""
    return get_display(arabic_reshaper.reshape(str(s)))


def pick_font() -> str:
    for cand in ("Tahoma", "Arial", "Segoe UI", "Times New Roman"):
        try:
            path = font_manager.findfont(cand, fallback_to_default=False)
            if os.path.exists(path):
                font_manager.fontManager.addfont(path)
                return cand
        except Exception:
            continue
    return "DejaVu Sans"


def to_fa(v) -> str:
    return str(v).translate(str.maketrans("0123456789", FA_DIGITS))


def num(v):
    try:
        return float(str(v).replace(",", "").replace("٬", "").replace("٫", ".").replace("،", ""))
    except (TypeError, ValueError):
        return None


def draw(spec: dict, outdir: str) -> str | None:
    kind = spec.get("kind", "line")
    x_raw = spec.get("x") or []
    series = [s for s in spec.get("series", []) if s.get("y")]
    if not x_raw or not series:
        return None

    xi = list(range(len(x_raw)))
    ys = [[num(v) for v in s["y"]] for s in series]
    n = min(len(xi), max(len(y) for y in ys))
    xi = xi[:n]
    ys = [y[:n] for y in ys]

    # سلول ناخوانا نباید matplotlib را بشکند؛ صفر می‌شود و شمارش می‌گردد
    missing = 0
    for y in ys:
        for k, v in enumerate(y):
            if v is None:
                y[k] = 0.0
                missing += 1
    if all(all(v == 0 for v in y) for y in ys):
        return None

    plt.rcParams["font.family"] = pick_font()
    fig, ax = plt.subplots(figsize=(7.4, 4.0), dpi=200)
    fig.patch.set_facecolor("white")

    if kind in ("bar",):
        width = 0.8 / max(1, len(ys))
        for k, (s, y) in enumerate(zip(series, ys, strict=False)):
            off = (k - (len(ys) - 1) / 2) * width
            ax.bar(
                [i + off for i in xi],
                y,
                width=width,
                label=fa(s["name"]),
                color=PALETTE[k % len(PALETTE)],
                edgecolor="white",
                linewidth=0.5,
            )
    elif kind in ("grouped_bar", "stacked_bar"):
        if kind == "stacked_bar":
            bottom = [0.0] * n
            for k, (s, y) in enumerate(zip(series, ys, strict=False)):
                ax.bar(
                    xi,
                    y,
                    0.68,
                    bottom=bottom,
                    label=fa(s["name"]),
                    color=PALETTE[k % len(PALETTE)],
                    edgecolor="white",
                    linewidth=0.5,
                )
                bottom = [b + (v or 0) for b, v in zip(bottom, y, strict=False)]
        else:
            width = 0.8 / max(1, len(ys))
            for k, (s, y) in enumerate(zip(series, ys, strict=False)):
                off = (k - (len(ys) - 1) / 2) * width
                ax.bar(
                    [i + off for i in xi],
                    y,
                    width=width,
                    label=fa(s["name"]),
                    color=PALETTE[k % len(PALETTE)],
                    edgecolor="white",
                    linewidth=0.5,
                )
    elif kind == "area":
        ax.stackplot(
            xi,
            ys,
            labels=[fa(s["name"]) for s in series],
            colors=[PALETTE[k % len(PALETTE)] for k in range(len(ys))],
            alpha=0.85,
        )
    elif kind == "scatter":
        for k, (s, y) in enumerate(zip(series, ys, strict=False)):
            ax.plot(
                xi, y, "o", label=fa(s["name"]), color=PALETTE[k % len(PALETTE)], markersize=4.5
            )
    else:
        for k, (s, y) in enumerate(zip(series, ys, strict=False)):
            ax.plot(
                xi,
                y,
                marker="o",
                markersize=3.4,
                linewidth=1.5,
                label=fa(s["name"]),
                color=PALETTE[k % len(PALETTE)],
            )

    ax.set_xticks(xi)
    ax.set_xticklabels([fa(v) for v in x_raw[:n]], fontsize=7.6)
    if spec.get("x_label"):
        ax.set_xlabel(fa(spec["x_label"]), fontsize=8.2)
    if spec.get("y_label"):
        ax.set_ylabel(fa(spec["y_label"]), fontsize=8.2)
    if spec.get("title"):
        ax.set_title(fa(spec["title"]), fontsize=9.4, pad=7)

    ax.grid(axis="y", linewidth=0.4, color="#d8d8d8", linestyle="-")
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.6)
        ax.spines[s].set_color("#666")

    if len(series) > 1:
        leg = ax.legend(
            fontsize=7.4, frameon=False, ncol=min(3, len(series)), loc="best", handlelength=1.5
        )
        for t in leg.get_texts():
            t.set_fontsize(7.4)

    if spec.get("conf"):
        note = spec["conf"]
        if missing:
            note += f"  ·  {missing} سلول ناخوانا صفر گرفته شده"
        fig.text(0.99, 0.015, fa(note), ha="right", va="bottom", fontsize=6.6, color="#7a1f1f")
    if spec.get("source"):
        fig.text(
            0.01, 0.015, fa(spec["source"]), ha="left", va="bottom", fontsize=6.6, color="#555"
        )

    fig.tight_layout(rect=(0, 0.045, 1, 1))
    os.makedirs(outdir, exist_ok=True)
    name = f"{spec.get('book', 'x')}__{spec['id']}.png"
    path = os.path.join(outdir, name)
    fig.savefig(path, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="")
    args = ap.parse_args()

    if not os.path.exists(DATA):
        print("figures_data.json یافت نشد — نموداری رسم نمی‌شود")
        print("جای‌نگهدار شکل‌ها در نسخهٔ چاپی فعال می‌ماند.")
        return 0

    with open(DATA, encoding="utf-8") as _fh:
        specs = json.load(_fh)
    if isinstance(specs, dict):
        specs = specs.get("specs", [])
    made = skipped = 0
    for spec in specs:
        if args.book and spec.get("book") != args.book:
            continue
        p = draw(spec, FIGDIR)
        if p:
            made += 1
            print(
                f"  رسم شد: {spec.get('book', '?'):<8} شکل {spec['id']:<8} {spec.get('kind', '')}"
            )
        else:
            skipped += 1
            print(f"  رد شد:  {spec.get('book', '?'):<8} شکل {spec.get('id', '?')} — داده ناکافی")
    print(f"\nرسم‌شده: {made}  ·  رد‌شده: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
