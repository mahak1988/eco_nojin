#!/usr/bin/env python3
"""
Seed legal texts from message files for all 14 languages.
Run after Phase 2 migration.
"""

import json
from pathlib import Path

from database.hub import hub
from database.models import LegalText

MESSAGES_DIR = Path("apps/web/messages")

# Legal text slugs and their message keys (directly under legal section)
LEGAL_TEXTS = {
    "terms": {"title": "termsTitle", "body": "termsBody"},
    "privacy": {"title": "privacyTitle", "body": "privacyBody"},
    "cookies": {"title": "cookiesTitle", "body": "cookiesBody"},
    "ecommerce_rules": {"title": "ecommerceRulesTitle", "body": "ecommerceRulesBody"},
    "buy_sell_rules": {"title": "buySellRulesTitle", "body": "buySellRulesBody"},
}


def get_nested(obj: dict, key: str, default: str = "") -> str:
    """Get value from dict (direct key, not nested)."""
    return obj.get(key, default)


def seed_legal_texts():
    """Seed legal texts from message files."""
    # Get all locale files
    locale_files = list(MESSAGES_DIR.glob("*.json"))
    print(f"Found {len(locale_files)} locale files")

    inserted = 0
    skipped = 0

    with hub.get_session() as session:
        for locale_file in locale_files:
            locale = locale_file.stem
            if locale == "meta":
                continue

            print(f"\nProcessing {locale}...")

            with open(locale_file, encoding="utf-8-sig") as f:
                messages = json.load(f)

            # Skip if no legal section
            if "legal" not in messages:
                print(f"  No legal section in {locale}")
                continue

            legal_section = messages["legal"]

            for slug, keys in LEGAL_TEXTS.items():
                title = get_nested(legal_section, keys["title"])
                body = get_nested(legal_section, keys["body"])

                if not title or not body:
                    print(f"  Skipping {slug} - missing title/body")
                    continue

                # Check if already exists
                existing = (
                    session.query(LegalText)
                    .filter(
                        LegalText.locale == locale, LegalText.slug == slug, LegalText.version == 1
                    )
                    .first()
                )

                if existing:
                    print(f"  Already exists: {locale}/{slug} v1")
                    skipped += 1
                    continue

                text = LegalText(
                    locale=locale,
                    slug=slug,
                    title=title,
                    body=body,
                    version=1,
                    status="published",
                )
                session.add(text)
                inserted += 1
                print(f"  Inserted: {locale}/{slug} v1 - {title[:50]}...")

        print(f"\nDone! Inserted: {inserted}, Skipped: {skipped}")


if __name__ == "__main__":
    seed_legal_texts()
