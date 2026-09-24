#!/usr/bin/env python3
"""
Seed script for Eco Nojin pilot data.
Creates realistic pilot data matching the actual database schema.
"""

import hashlib
import sqlite3
import uuid
from datetime import datetime

DB_PATH = "D:/eco_nojin/data/econojin.db"


def gen_id():
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


PILOT_USERS = [
    {
        "email": "admin@econojin.org",
        "username": "admin",
        "full_name": "مدیر سامانه اکو نوژین",
        "role": "admin",
        "language": "fa",
        "phone": "+989000000001",
        "country": "Iran",
        "city": "Tehran",
    },
    {
        "email": "ahmad.mohammadi@farmer.ir",
        "username": "ahmad.mohammadi",
        "full_name": "احمد محمدی",
        "role": "farmer",
        "language": "fa",
        "phone": "+989123456789",
        "country": "Iran",
        "city": "Gorgan",
    },
    {
        "email": "maryam.rezaei@farmer.ir",
        "username": "maryam.rezaei",
        "full_name": "مریم رضایی",
        "role": "farmer",
        "language": "fa",
        "phone": "+989123456790",
        "country": "Iran",
        "city": "Neyshabur",
    },
    {
        "email": "khani.ghashghai@nomad.ir",
        "username": "khani.ghashghai",
        "full_name": "خانی قشقایی",
        "role": "farmer",
        "language": "fa",
        "phone": "+989123456791",
        "country": "Iran",
        "city": "Sepidan",
    },
    {
        "email": "reza.ahmadi@farmer.ir",
        "username": "reza.ahmadi",
        "full_name": "رضا احمدی",
        "role": "farmer",
        "language": "fa",
        "phone": "+989123456792",
        "country": "Iran",
        "city": "Anzali",
    },
    {
        "email": "fatemeh.karimi@farmer.ir",
        "username": "fatemeh.karimi",
        "full_name": "فاطمه کریمی",
        "role": "farmer",
        "language": "fa",
        "phone": "+989123456793",
        "country": "Iran",
        "city": "Rafsanjan",
    },
    {
        "email": "inspector@doe.ir",
        "username": "inspector",
        "full_name": "مفتش سازمان محیط زیست",
        "role": "institution",
        "language": "fa",
        "phone": "+989123456794",
        "country": "Iran",
        "city": "Tehran",
    },
    {
        "email": "researcher@university.ac.ir",
        "username": "researcher",
        "full_name": "دکتر محمد رضایی",
        "role": "researcher",
        "language": "fa",
        "phone": "+989123456795",
        "country": "Iran",
        "city": "Tehran",
    },
]

# Land profiles matching the actual schema
PILOT_LAND_PROFILES = [
    {
        "name": "مزرعه گندم ارگانیک گلستان",
        "description": "مزرعه ۱۲۰ هکتاری گندم ارگانیک در شهرستان گرگان با سیستم آبیاری قطره‌ای",
        "location_lat": 36.8419,
        "location_lon": 54.4417,
        "area_ha": 120.5,
        "dem_source": "SRTM",
        "dem_resolution_m": 30.0,
    },
    {
        "name": "باغ زعفران خراسان رضوی",
        "description": "باغ ۱۵ هکتاری زعفران در نیشبور با روش‌های سنتی و ارگانیک",
        "location_lat": 36.2134,
        "location_lon": 58.7956,
        "area_ha": 15.2,
        "dem_source": "SRTM",
        "dem_resolution_m": 30.0,
    },
    {
        "name": "مرتع‌های عشایری قشقایی فارس",
        "description": "مرتع‌های عشایری قشقایی برای گدام‌های لبنی در کوه‌های زاگرس",
        "location_lat": 30.2583,
        "location_lon": 51.9856,
        "area_ha": 500.0,
        "dem_source": "SRTM",
        "dem_resolution_m": 30.0,
    },
    {
        "name": "مزرعه برنج انزلی",
        "description": "مزرعه ۸۰ هکتاری برنج در آنزلی با سیستم آب‌بندی سنتی",
        "location_lat": 37.4767,
        "location_lon": 49.4689,
        "area_ha": 80.0,
        "dem_source": "SRTM",
        "dem_resolution_m": 30.0,
    },
    {
        "name": "باغ‌های پسته کرمان",
        "description": "باغ ۴۰ هکتاری پسته در رافسنجان با آبیاری زیرزمینی",
        "location_lat": 30.4000,
        "location_lon": 56.0000,
        "area_ha": 40.5,
        "dem_source": "SRTM",
        "dem_resolution_m": 30.0,
    },
]

PILOT_MARKETPLACES = [
    {
        "name": "بازارگاه منطقه گلستان",
        "slug": "golestan-marketplace",
        "description": "بازارگاه منطقه‌ای برای عرضه محصولات ارگانیک و سنتی گلستان",
        "marketplace_type": "regional",
        "address": "گرگان، بلوار آیت‌الله هاشمی، خیابان شهید بهشتی",
        "contact_email": "golestan@econojin.org",
        "contact_phone": "+981733334455",
        "village_id": "golestan-village-001",
    },
    {
        "name": "بازارگاه خراسان رضوی",
        "slug": "khorasan-razavi-marketplace",
        "description": "بازارگاه منطقه‌ای زعفران، پسته و میوه‌های خشک خراسان",
        "marketplace_type": "regional",
        "address": "مشهد، بلوار امام رضا، کوچه علم",
        "contact_email": "khorasan@econojin.org",
        "contact_phone": "+985138445566",
        "village_id": "khorasan-village-001",
    },
    {
        "name": "بازارگاه فارس",
        "slug": "fars-marketplace",
        "description": "بازارگاه منطقه‌ای محصولات لبنی عشایری و گیاهان دارویی فارس",
        "marketplace_type": "regional",
        "address": "شیراز، بزرگراه صدر، مجتمع تجاری ایران",
        "contact_email": "fars@econojin.org",
        "contact_phone": "+987132223344",
        "village_id": "fars-village-001",
    },
]

PILOT_PRODUCTS = [
    {
        "name": "گندم ارگانیک گلستان",
    },
    {
        "name": "زعفران نگین مرغوب",
    },
    {
        "name": "ماست و پنیر عشایری قشقایی",
    },
    {
        "name": "برنج انزلی",
    },
    {
        "name": "پسته اکبری رفسنجانی",
    },
]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    print("Seeding pilot data...")

    # 1. Seed auth_users
    user_id_map = {}
    password_hash = hash_password("EcoNojin2024!")
    now = datetime.now().isoformat()

    for u in PILOT_USERS:
        uid = gen_id()
        cursor.execute(
            """
            INSERT OR IGNORE INTO auth_users (id, email, username, password_hash, is_active, is_verified, failed_login_attempts, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (uid, u["email"], u["username"], password_hash, True, True, 0, now, now),
        )
        user_id_map[u["email"]] = uid

    # Also insert into users table
    for u in PILOT_USERS:
        uid = user_id_map[u["email"]]
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (id, email, hashed_password, full_name, phone, country, city, language, role, is_email_verified, is_active, two_factor_enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                uid,
                u["email"],
                hash_password("EcoNojin2024!"),
                u["full_name"],
                u["phone"],
                u["country"],
                u["city"],
                u["language"],
                u["role"],
                True,
                True,
                False,
                now,
            ),
        )

    print(f"Seeded {len(user_id_map)} users")

    # 2. Seed land_profiles
    user_emails = list(user_id_map.keys())
    farmer_emails = [e for e in user_emails if "farmer" in e or "nomad" in e]

    for i, land in enumerate(PILOT_LAND_PROFILES):
        farmer_emails[i % len(farmer_emails)]
        uid = gen_id()
        cursor.execute(
            """
            INSERT INTO land_profiles (id, name, description, location_lat, location_lon, area_ha, dem_source, dem_resolution_m, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                uid,
                land["name"],
                land["description"],
                land["location_lat"],
                land["location_lon"],
                land["area_ha"],
                land["dem_source"],
                land["dem_resolution_m"],
                user_id_map[farmer_emails[i % len(farmer_emails)]],
                datetime.now().isoformat(),
            ),
        )

    print(f"Seeded {len(PILOT_LAND_PROFILES)} land profiles")

    # 3. Seed marketplaces
    marketplace_id_map = {}
    for mp in PILOT_MARKETPLACES:
        mid = gen_id()
        cursor.execute(
            """
            INSERT INTO marketplaces (
                id, name, slug, description, marketplace_type, address, contact_email, contact_phone,
                village_id, marketplace_type, e_commerce_rules_accepted, buy_sell_rules_accepted,
                identity_verified, admin_approved, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                mid,
                mp["name"],
                mp["slug"],
                mp["description"],
                mp["marketplace_type"],
                mp["address"],
                mp["contact_email"],
                mp["contact_phone"],
                mp["village_id"],
                mp["marketplace_type"],
                True,
                True,
                True,
                True,
                "active",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        marketplace_id_map[mp["name"]] = mid

    print(f"Seeded {len(marketplace_id_map)} marketplaces")

    # 4. Seed products (basic)
    for prod in PILOT_PRODUCTS:
        cursor.execute("INSERT OR IGNORE INTO product (name) VALUES (?)", (prod["name"],))

    print(f"Seeded {len(PILOT_PRODUCTS)} products")

    # 5. Seed marketplace commission rules
    for _mp_name, mp_id in marketplace_id_map.items():
        cursor.execute(
            """
            INSERT OR IGNORE INTO marketplace_commission_rules (id, village_id, category, platform_fee_bps, landscape_fee_bps, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (gen_id(), mp_id.split("-")[0], "default", 300, 100, True, datetime.now().isoformat()),
        )

    conn.commit()
    conn.close()
    print("Seeding completed successfully!")


def clean_test_data():
    """Remove any test records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tables validated against known schema
    VALID_TABLES_WITH_NAME = {"land_profiles", "product", "marketplaces", "carbon_projects"}
    VALID_TABLES_WITH_EMAIL = {"auth_users", "users"}

    for table in VALID_TABLES_WITH_NAME:
        try:
            cursor.execute(
                'DELETE FROM {} WHERE name LIKE ? OR name LIKE ? OR name LIKE ?'.format(table),
                ("%test%", "%Test%", "%TEST%")
            )
            if cursor.rowcount:
                print(f"Cleaned {cursor.rowcount} test records from {table}")
        except sqlite3.OperationalError as e:
            print(f"Skipped {table}: {e}")

    for table in VALID_TABLES_WITH_EMAIL:
        try:
            cursor.execute(
                'DELETE FROM {} WHERE email LIKE ? OR email LIKE ?'.format(table),
                ("%test%", "%Test%")
            )
            if cursor.rowcount:
                print(f"Cleaned {cursor.rowcount} test records from {table}")
        except sqlite3.OperationalError as e:
            print(f"Skipped {table}: {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    clean_test_data()
    seed_database()
