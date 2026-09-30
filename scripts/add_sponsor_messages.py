"""Insert the sponsors block into a next-intl message file.

next-intl is strict: a message file must have identical key sets across
locales or it fails at render time. So the check is not "does en have it" but
"do all locales have the same keys". This script enforces that after every
insert, which is the failure mode that only shows up in the browser.

Usage:  python scripts/add_sponsor_messages.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MESSAGES = REPO / "apps" / "web" / "messages"

EN = {
    "region_label": "Sponsorship disclosure",
    "disclosure": "This section is funded by {sponsor}.",
    "policy_title": "Sponsorship policy",
    "policy_intro": (
        "Sponsorship is recognition by a named funder of work this platform "
        "carries out. It is not advertising."
    ),
    "no_ads": (
        "We do not run programmatic advertising. There is no advertising "
        "network, no third-party advertising SDK, no impression counter and no "
        "behavioural targeting anywhere in this product."
    ),
    "no_targeting": (
        "The sponsorship response carries no user, device or referrer data, so "
        "a slot cannot be personalised."
    ),
    "contextual": (
        "A slot appears only on a page about a service the sponsor funded. It "
        "never appears beside a recommendation we give a farmer."
    ),
    "no_advisory": (
        "There is no slot on any agronomic, checkout, settlement or low-bandwidth surface."
    ),
    "transparency": (
        "Every current sponsor is listed on this page, including any that was "
        "suspended or terminated, and the reason."
    ),
    "green_claims": (
        "Each sponsor re-attests quarterly that its own environmental claims "
        "remain substantiated. A sponsor that does not is suspended."
    ),
    "become": "Become a sponsor",
    "current_sponsors": "Current sponsors",
    "none": "There are no current sponsors.",
}

FA = {
    "region_label": "افشای حمایت مالی",
    "disclosure": "این بخش با حمایت مالی {sponsor} تأمین شده است.",
    "policy_title": "سیاست اسپانسرشیپ",
    "policy_intro": (
        "اسپانسرشیپ یعنی شناخته‌شدن یک حامی نام‌دار برای کاری که این پلتفرم انجام می‌دهد. تبلیغ نیست."
    ),
    "no_ads": (
        "ما تبلیغات الگوریتمی اجرا نمی‌کنیم. هیچ شبکهٔ تبلیغاتی، هیچ SDK "
        "تبلیغاتی شخص ثالث، هیچ شمارندهٔ نمایش و هیچ تارگتینگ رفتاری در این "
        "محصول وجود ندارد."
    ),
    "no_targeting": (
        "پاسخ اسپانسرشیپ هیچ دادهٔ کاربر، دستگاه یا ارجاع ندارد، بنابراین "
        "جای تبلیغ قابل شخصی‌سازی نیست."
    ),
    "contextual": (
        "جای تبلیغ فقط در صفحهٔ خدمتی ظاهر می‌شود که حامی آن را تأمین کرده. "
        "هرگز کنار توصیه‌ای که به کشاورز می‌دهیم ظاهر نمی‌شود."
    ),
    "no_advisory": ("هیچ جای تبلیغی روی سطوح زراعی، پرداخت، تسویه یا کم‌پهنا‌باند وجود ندارد."),
    "transparency": (
        "همهٔ حامیان فعلی در این صفحه فهرست می‌شوند، از جمله هر حامی که تعلیق "
        "یا خاتمه یافته، به‌همراه دلیل."
    ),
    "green_claims": (
        "هر حامی هر سه ماه دوباره تأیید می‌کند که ادعاهای زیست‌محیطی خودش "
        "همچنان مستند است. حامی‌ای که این کار را نکند تعلیق می‌شود."
    ),
    "become": "حامی شوید",
    "current_sponsors": "حامیان فعلی",
    "none": "در حال حاضر هیچ حامی‌ای وجود ندارد.",
}


def main() -> int:
    changed: list[str] = []
    for locale, block in (("en", EN), ("fa", FA)):
        path = MESSAGES / f"{locale}.json"
        if not path.exists():
            print(f"skip: {path} not found", file=sys.stderr)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("sponsors") == block:
            continue
        data["sponsors"] = block
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed.append(locale)

    print(f"updated: {changed or 'nothing'}")

    # next-intl fails at render if locales disagree. Verify.
    def keys(obj: dict, prefix: str = "") -> set[str]:
        out: set[str] = set()
        for k, v in obj.items():
            path = f"{prefix}{k}"
            if isinstance(v, dict):
                out |= keys(v, f"{path}.")
            else:
                out.add(path)
        return out

    en_data = json.loads((MESSAGES / "en.json").read_text(encoding="utf-8"))
    fa_data = json.loads((MESSAGES / "fa.json").read_text(encoding="utf-8"))
    only_en = sorted(keys(en_data) - keys(fa_data))
    only_fa = sorted(keys(fa_data) - keys(en_data))
    sponsors_gap = [k for k in only_en if k.startswith("sponsors.")] + [
        k for k in only_fa if k.startswith("sponsors.")
    ]

    if sponsors_gap:
        print(f"SPONSOR KEY MISMATCH: {sponsors_gap}", file=sys.stderr)
        return 1

    total_other = len([k for k in only_en + only_fa if not k.startswith("sponsors.")])
    print("sponsor keys aligned across en/fa")
    print(f"pre-existing non-sponsor key drift: {total_other} (not our scope)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
