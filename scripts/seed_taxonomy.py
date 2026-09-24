#!/usr/bin/env python3
"""
Seed 3-level product category taxonomy for Phase 2 marketplace.
Hierarchy: Level 1 (Top) -> Level 2 (Category) -> Level 3 (Subcategory)
"""

import sqlite3
from datetime import datetime

DB_PATH = "D:/eco_nojin/data/econojin.db"

# 3-level taxonomy for Iranian agricultural/products marketplace
TAXONOMY = [
    # Level 1: محصولات کشاورزی (Agricultural Products)
    {
        "code": "AGR",
        "name": "محصولات کشاورزی",
        "description": "محصولات اولیه کشاورزی، باغی ودامی",
        "level": 1,
        "parent_code": None,
        "children": [
            # Level 2: غلات و حبوبات
            {
                "code": "AGR-GRAIN",
                "name": "غلات و حبوبات",
                "description": "گندم، برنج، جو، ذرت، حبوبات",
                "level": 2,
                "parent_code": "AGR",
                "children": [
                    {
                        "code": "AGR-GRAIN-WHT",
                        "name": "گندم",
                        "description": "گندم پنچ، گندم معمولی، گندم درخشان",
                        "level": 3,
                    },
                    {
                        "code": "AGR-GRAIN-RIC",
                        "name": "برنج",
                        "description": "برنج دوم، برنج اول، برنج قندی، برنج جشن",
                        "level": 3,
                    },
                    {
                        "code": "AGR-GRAIN-BAR",
                        "name": "جو",
                        "description": "جو دو ردیفه، جو شش ردیفه، جو علفی",
                        "level": 3,
                    },
                    {
                        "code": "AGR-GRAIN-CRN",
                        "name": "ذرت",
                        "description": "ذرت دانه، ذرت علفی، ذرت شیرین",
                        "level": 3,
                    },
                    {
                        "code": "AGR-GRAIN-PUL",
                        "name": "حبوبات",
                        "description": "نخود، لوبیا، عدس، ماش، لپه",
                        "level": 3,
                    },
                ],
            },
            # Level 2: میوه‌ها
            {
                "code": "AGR-FRUIT",
                "name": "میوه‌ها",
                "description": "میوه‌های خوشه‌ای، هسته‌ای، موسمی",
                "level": 2,
                "parent_code": "AGR",
                "children": [
                    {
                        "code": "AGR-FRUIT-CIT",
                        "name": "موسمی و پرتقال",
                        "description": "موسمی، پرتقال، لیمو، گراپ‌فروت",
                        "level": 3,
                    },
                    {
                        "code": "AGR-FRUIT-STO",
                        "name": "میوه‌های هسته‌ای",
                        "description": "سیب، گلابی، به، هلو، آلو، زردآلو",
                        "level": 3,
                    },
                    {
                        "code": "AGR-FRUIT-BER",
                        "name": "میوه‌های باریک",
                        "description": "توت، کلم، انار، خرما، انگور",
                        "level": 3,
                    },
                    {
                        "code": "AGR-FRUIT-TRO",
                        "name": "میوه‌های استوایی",
                        "description": "موز، اناناس، پاپایا، خیوی، آوکادو",
                        "level": 3,
                    },
                ],
            },
            # Level 2: سبزیجات
            {
                "code": "AGR-VEG",
                "name": "سبزیجات",
                "description": "سبزیجات برگی، ریشه‌ای، ثمری",
                "level": 2,
                "parent_code": "AGR",
                "children": [
                    {
                        "code": "AGR-VEG-LEA",
                        "name": "سبزیجات برگی",
                        "description": "اسفناج، جعفری، کرفس، کاهو، سبزی خرد",
                        "level": 3,
                    },
                    {
                        "code": "AGR-VEG-ROO",
                        "name": "سبزیجات ریشه‌ای",
                        "description": "سیب‌زمینی، هویج، گردو، بنجر، شلغم",
                        "level": 3,
                    },
                    {
                        "code": "AGR-VEG-FRU",
                        "name": "سبزیجات ثمری",
                        "description": "گوجه‌فرنگی، باذنجان، فلفل، کدو، خیار",
                        "level": 3,
                    },
                    {
                        "code": "AGR-VEG-ALL",
                        "name": "گیاهان تریاقی",
                        "description": "سیر، پیاز، تریاق، زیره، نعنا",
                        "level": 3,
                    },
                ],
            },
            # Level 2: محصولاتدامی
            {
                "code": "AGR-LIVE",
                "name": "محصولات دام و طیور",
                "description": "گوشت، لبنیات، تخم‌مرغ، عسل",
                "level": 2,
                "parent_code": "AGR",
                "children": [
                    {
                        "code": "AGR-LIVE-MEA",
                        "name": "گوشت",
                        "description": "گوشت گوساله، گوسفندی، مرغ، گاوی",
                        "level": 3,
                    },
                    {
                        "code": "AGR-LIVE-DAI",
                        "name": "لبنیات",
                        "description": "شیر، ماست، پنیر، کره، دوغ",
                        "level": 3,
                    },
                    {
                        "code": "AGR-LIVE-EGG",
                        "name": "تخم‌مرغ",
                        "description": "تخم‌مرغ مرغ، تخم‌مرغ قالی، تخم‌مرغ ارگانیک",
                        "level": 3,
                    },
                    {
                        "code": "AGR-LIVE-HON",
                        "name": "عسل و محصولات ارده",
                        "description": "عسل طبیعی، ارده، شیره، رب انار",
                        "level": 3,
                    },
                ],
            },
        ],
    },
    # Level 1: مصنوعات غذایی (Processed Foods)
    {
        "code": "PROC",
        "name": "مصنوعات غذایی",
        "description": "محصولات پردازش، بسته‌بندی و تبدیل شده",
        "level": 1,
        "parent_code": None,
        "children": [
            {
                "code": "PROC-DRY",
                "name": "خشکبار و میوه‌های خشک",
                "description": "پسته، بادام، گردو، آجیل، میوه‌های خشک",
                "level": 2,
                "parent_code": "PROC",
                "children": [
                    {
                        "code": "PROC-DRY-NUT",
                        "name": "آجیل و خشکبار",
                        "description": "پسته، بادام، گردو، چيلگوزا، فندق",
                        "level": 3,
                    },
                    {
                        "code": "PROC-DRY-FRU",
                        "name": "میوه‌های خشک",
                        "description": "خرما، توت‌فرنگی، آلو خشک، بی‌دیده، انار خشک",
                        "level": 3,
                    },
                ],
            },
            {
                "code": "PROC-SPI",
                "name": "ادویه و چای",
                "description": "زعفران، چای، ادویه‌های سنتی و صنعتی",
                "level": 2,
                "parent_code": "PROC",
                "children": [
                    {
                        "code": "PROC-SPI-SAF",
                        "name": "زعفران",
                        "description": "زعفران نگین، سرقل، pousser، دسته",
                        "level": 3,
                    },
                    {
                        "code": "PROC-SPI-TEA",
                        "name": "چای",
                        "description": "چای سیاه، چای سبز، چای گیاهی، چای برگ",
                        "level": 3,
                    },
                    {
                        "code": "PROC-SPI-SPI",
                        "name": "ادویه‌ها",
                        "description": "فلفل سیاه، زیره، هیل، دارچین، گرده گل، سیر پودر",
                        "level": 3,
                    },
                ],
            },
            {
                "code": "PROC-CAN",
                "name": "مربا، عسل و مربیات",
                "description": "مرباهای سنتی، عسل طبیعی، شیره، رب",
                "level": 2,
                "parent_code": "PROC",
                "children": [
                    {
                        "code": "PROC-CAN-JAM",
                        "name": "مربا",
                        "description": "مربای سیب، پرتقال، توت، آلو، هلو، گلابی",
                        "level": 3,
                    },
                    {
                        "code": "PROC-CAN-HON",
                        "name": "عسل و شیره",
                        "description": "عسل طبیعی، شیره انگور، شیره خرما، رب انار",
                        "level": 3,
                    },
                ],
            },
        ],
    },
    # Level 1: صنعت و دستی‌دود (Handicrafts & Industrial)
    {
        "code": "CRAFT",
        "name": "صنایع دستی و صنعت",
        "description": "فرش، گلدوزی، سرامیک، چرم، فلزات",
        "level": 1,
        "parent_code": None,
        "children": [
            {
                "code": "CRAFT-TEX",
                "name": "بافندگی و فرش",
                "description": "فرش دست‌باف، جاجیم، گلیم، قالیچه، ترمه",
                "level": 2,
                "parent_code": "CRAFT",
                "children": [
                    {
                        "code": "CRAFT-TEX-CAR",
                        "name": "فرش و قالیچه",
                        "description": "فرش تبریزی، فرش کاشانی، فرش قمی، فرش بلوچی",
                        "level": 3,
                    },
                    {
                        "code": "CRAFT-TEX-KIL",
                        "name": "گلیم و جاجیم",
                        "description": "گلیم شمالی، جاجیم اراک، سommée، ورنی",
                        "level": 3,
                    },
                ],
            },
            {
                "code": "CRAFT-POT",
                "name": "سفال و سرامیک",
                "description": "ظرف‌های سفالی، کاشی، سفالینه، چینی",
                "level": 2,
                "parent_code": "CRAFT",
                "children": [
                    {
                        "code": "CRAFT-POT-POT",
                        "name": "ظرف‌های سفالی",
                        "description": "دیگ چتی، كاب سفالی، قوری، البشريه، asko",
                        "level": 3,
                    },
                    {
                        "code": "CRAFT-POT-TIL",
                        "name": "کاشی و سرامیک",
                        "description": "کاشی هفت‌رنگ، کاشی معرق، کاشی موزاییک",
                        "level": 3,
                    },
                ],
            },
            {
                "code": "CRAFT-MET",
                "name": "فلزات و آهن‌کاری",
                "description": "قلم‌زنی، مشغله‌سازی، آهن‌کاری سنتی",
                "level": 2,
                "parent_code": "CRAFT",
                "children": [
                    {
                        "code": "CRAFT-MET-ENG",
                        "name": "قلم‌زنی",
                        "description": "قلم‌زنی بر روی مس، برنج، نقره، طلا",
                        "level": 3,
                    },
                    {
                        "code": "CRAFT-MET-BLA",
                        "name": "آهن‌کاری",
                        "description": "درب‌بندی، درب‌چی، قفل‌سازی، مشغله‌سازی",
                        "level": 3,
                    },
                ],
            },
        ],
    },
    # Level 1: خدمات (Services)
    {
        "code": "SERV",
        "name": "خدمات",
        "description": "خدمات کشاورزی، فنی، آموزشی و مشاوره",
        "level": 1,
        "parent_code": None,
        "children": [
            {
                "code": "SERV-AGR",
                "name": "خدمات کشاورزی",
                "description": "مشاوره آبیاری، کاشت، برداشت، مبارزه آفات",
                "level": 2,
                "parent_code": "SERV",
                "children": [
                    {
                        "code": "SERV-AGR-IRR",
                        "name": "طراحی و اجرای آبیاری",
                        "description": "سیستم‌های قطره‌ای، فواره‌ای، زیرزمینی",
                        "level": 3,
                    },
                    {
                        "code": "SERV-AGR-PES",
                        "name": "مدیریت آفات و بیماری‌ها",
                        "description": "پایش، پیشگیری، درمان یکپارچه (IPM)",
                        "level": 3,
                    },
                ],
            },
            {
                "code": "SERV-TEC",
                "name": "خدمات فنی و مهندسی",
                "description": "نقشه‌برداری، آزمایش خاک، طراحی لوله‌کشی",
                "level": 2,
                "parent_code": "SERV",
                "children": [
                    {
                        "code": "SERV-TEC-SOI",
                        "name": "آزمایش خاک و آب",
                        "description": "تحلیل پH، EC، مواد مغذی، سموم",
                        "level": 3,
                    },
                    {
                        "code": "SERV-TEC-MAP",
                        "name": "نقشه‌برداری و GIS",
                        "description": "نقشه‌برداری الأرضی، پهنه‌بندی اراضی",
                        "level": 3,
                    },
                ],
            },
        ],
    },
]


def clear_existing():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inv_category")
    conn.commit()
    conn.close()
    print("Cleared existing categories")


def seed_taxonomy():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    datetime.now().isoformat()
    inserted = 0

    def insert_cat(cat, parent_id=None):
        nonlocal inserted
        cursor.execute(
            """
            INSERT INTO inv_category (code, name, description, parent_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                cat["code"],
                cat["name"],
                cat["description"],
                parent_id,
                True,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        cat_id = cursor.lastrowid
        inserted += 1

        if "children" in cat:
            for child in cat["children"]:
                insert_cat(child, cat_id)

    for top_cat in TAXONOMY:
        insert_cat(top_cat)

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} categories")


def verify():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM inv_category")
    total = cursor.fetchone()[0]
    print(f"\nTotal categories: {total}")

    cursor.execute(
        "SELECT level, COUNT(*) FROM (SELECT CASE WHEN parent_id IS NULL THEN 1 WHEN parent_id IN (SELECT id FROM inv_category WHERE parent_id IS NULL) THEN 2 ELSE 3 END as level FROM inv_category) GROUP BY level"
    )
    for row in cursor.fetchall():
        print(f"  Level {row[0]}: {row[1]} categories")

    # Show tree
    cursor.execute("SELECT id, code, name, parent_id FROM inv_category ORDER BY level, code")
    rows = cursor.fetchall()
    print("\nCategory tree:")
    for r in rows:
        indent = "  " * (0 if r[3] is None else (1 if r[3] < 100 else 2))
        print(f"{indent}{r[1]} - {r[2]} (parent={r[3]})")

    conn.close()


if __name__ == "__main__":
    clear_existing()
    seed_taxonomy()
    verify()
