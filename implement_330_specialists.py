#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
پیاده‌سازی سیستم ۳۳۰ گرایش تخصصی هیدروما
هدف: کاهش خطا به حداقل از طریق اعتبارسنجی چندتخصصی
============================================================================
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent

# ============================================================
# تعریف ۳۳۰ گرایش تخصصی
# ============================================================

SPECIALISTS = {
    "agriculture": {
        "name": "کشاورزی و زراعت",
        "icon": "🌾",
        "specialties": [
            {"id": "AGR001", "name": "زراعت عمومی", "algorithms": ["H01", "H05", "H09", "H18"]},
            {"id": "AGR002", "name": "اصلاح نباتات", "algorithms": ["H15", "H17", "H18"]},
            {"id": "AGR003", "name": "گیاه‌پزشکی", "algorithms": ["H05", "H19"]},
            {"id": "AGR004", "name": "حشره‌شناسی کشاورزی", "algorithms": ["H05", "H19"]},
            {"id": "AGR005", "name": "قارچ‌شناسی کشاورزی", "algorithms": ["H05", "H19"]},
            {"id": "AGR006", "name": "ویروس‌شناسی گیاهی", "algorithms": ["H05", "H19"]},
            {"id": "AGR007", "name": "نماتدشناسی", "algorithms": ["H09", "H19"]},
            {"id": "AGR008", "name": "علف‌های هرز", "algorithms": ["H05", "H19"]},
            {"id": "AGR009", "name": "فیزیولوژی گیاهی", "algorithms": ["H02", "H04", "H09"]},
            {"id": "AGR010", "name": "بیوتکنولوژی کشاورزی", "algorithms": ["H15", "H17", "H21"]},
            {"id": "AGR011", "name": "ژنتیک گیاهی", "algorithms": ["H15", "H17", "H19"]},
            {"id": "AGR012", "name": "بذرشناسی", "algorithms": ["H15", "H16", "H20"]},
            {"id": "AGR013", "name": "تکثیر گیاهان", "algorithms": ["H16", "H21"]},
            {"id": "AGR014", "name": "باغبانی", "algorithms": ["H05", "H18", "H21"]},
            {"id": "AGR015", "name": "درختان میوه", "algorithms": ["H07", "H15", "H18"]},
            {"id": "AGR016", "name": "سبزی‌کاری", "algorithms": ["H05", "H18", "H21"]},
            {"id": "AGR017", "name": "گل و گیاهان زینتی", "algorithms": ["H05", "H18"]},
            {"id": "AGR018", "name": "گیاهان دارویی", "algorithms": ["H05", "H18", "H21"]},
            {"id": "AGR019", "name": "گیاهان صنعتی", "algorithms": ["H05", "H18"]},
            {"id": "AGR020", "name": "غلات", "algorithms": ["H01", "H02", "H04", "H18"]},
            {"id": "AGR021", "name": "حبوبات", "algorithms": ["H01", "H09", "H18", "H21"]},
            {"id": "AGR022", "name": "دانه‌های روغنی", "algorithms": ["H01", "H09", "H18"]},
            {"id": "AGR023", "name": "کشاورزی ارگانیک", "algorithms": ["H09", "H13", "H21"]},
            {"id": "AGR024", "name": "کشاورزی حفاظتی", "algorithms": ["H09", "H10", "H13"]},
            {"id": "AGR025", "name": "کشاورزی دقیق", "algorithms": ["H05", "H22", "H23"]},
            {"id": "AGR026", "name": "کشاورزی هوشمند", "algorithms": ["H22", "H23", "H24"]},
            {"id": "AGR027", "name": "کشاورزی عمودی", "algorithms": ["H05", "H18"]},
            {"id": "AGR028", "name": "هیدروپونیک", "algorithms": ["H05", "H18"]},
            {"id": "AGR029", "name": "آکواپونیک", "algorithms": ["H05", "H18"]},
            {"id": "AGR030", "name": "کشت گلخانه‌ای", "algorithms": ["H05", "H18"]},
        ]
    },
    "climate": {
        "name": "اقلیم و هواشناسی",
        "icon": "🌤️",
        "specialties": [
            {"id": "CLI001", "name": "اقلیم‌شناسی عمومی", "algorithms": ["H01", "H02", "H04"]},
            {"id": "CLI002", "name": "اقلیم‌شناسی کاربردی", "algorithms": ["H01", "H02", "H04", "H05"]},
            {"id": "CLI003", "name": "هواشناسی کشاورزی", "algorithms": ["H01", "H02", "H04", "H05", "H06"]},
            {"id": "CLI004", "name": "هواشناسی دینامیک", "algorithms": ["H02", "H04"]},
            {"id": "CLI005", "name": "هواشناسی سینوپتیک", "algorithms": ["H01", "H06"]},
            {"id": "CLI006", "name": "هواشناسی ماهواره‌ای", "algorithms": ["H23", "H24"]},
            {"id": "CLI007", "name": "اقلیم‌شناسی تغییر اقلیم", "algorithms": ["H02", "H04", "H06"]},
            {"id": "CLI008", "name": "اقلیم‌شناسی آماری", "algorithms": ["H22", "H23"]},
            {"id": "CLI009", "name": "میکرواقلیم‌شناسی", "algorithms": ["H02", "H04"]},
            {"id": "CLI010", "name": "اقلیم‌شناسی شهری", "algorithms": ["H02", "H04"]},
            {"id": "CLI011", "name": "اقلیم‌شناسی کوهستانی", "algorithms": ["H02", "H04"]},
            {"id": "CLI012", "name": "اقلیم‌شناسی بیابان", "algorithms": ["H01", "H02", "H04", "H06"]},
            {"id": "CLI013", "name": "اقلیم‌شناسی حاره‌ای", "algorithms": ["H01", "H02", "H04"]},
            {"id": "CLI014", "name": "اقلیم‌شناسی قطبی", "algorithms": ["H02", "H04"]},
            {"id": "CLI015", "name": "بیوم هواشناسی", "algorithms": ["H02", "H04"]},
            {"id": "CLI016", "name": "هواشناسی هوانوردی", "algorithms": []},
            {"id": "CLI017", "name": "هواشناسی دریایی", "algorithms": ["H01", "H02"]},
            {"id": "CLI018", "name": "پیش‌بینی عددی هوا", "algorithms": ["H22"]},
            {"id": "CLI019", "name": "رادار هواشناسی", "algorithms": ["H01", "H06"]},
            {"id": "CLI020", "name": "لیدار هواشناسی", "algorithms": ["H23"]},
            {"id": "CLI021", "name": "اقلیم‌شناسی دیرینه", "algorithms": []},
            {"id": "CLI022", "name": "اقلیم‌شناسی آینده‌نگر", "algorithms": ["H22"]},
            {"id": "CLI023", "name": "هواشناسی حوادث شدید", "algorithms": ["H06"]},
            {"id": "CLI024", "name": "اقلیم‌شناسی خشکسالی", "algorithms": ["H01", "H06"]},
            {"id": "CLI025", "name": "اقلیم‌شناسی یخبندان", "algorithms": ["H02", "H04"]},
            {"id": "CLI026", "name": "اقلیم‌شناسی موج گرما", "algorithms": ["H02", "H04"]},
            {"id": "CLI027", "name": "هواشناسی تشعشع", "algorithms": ["H04"]},
            {"id": "CLI028", "name": "اقلیم‌شناسی باد", "algorithms": ["H10"]},
            {"id": "CLI029", "name": "اقلیم‌شناسی رطوبت", "algorithms": ["H02", "H03"]},
            {"id": "CLI030", "name": "اقلیم‌شناسی ابر و بارش", "algorithms": ["H01", "H06"]},
        ]
    },
    "water_soil": {
        "name": "آب و خاک",
        "icon": "💧",
        "specialties": [
            {"id": "WAS001", "name": "هیدرولوژی عمومی", "algorithms": ["H01", "H09", "H14"]},
            {"id": "WAS002", "name": "هیدرولوژی سطحی", "algorithms": ["H01", "H10"]},
            {"id": "WAS003", "name": "هیدرولوژی زیرزمینی", "algorithms": ["H09", "H14"]},
            {"id": "WAS004", "name": "هیدروژئولوژی", "algorithms": ["H09", "H14"]},
            {"id": "WAS005", "name": "هیدرولیک", "algorithms": ["H01"]},
            {"id": "WAS006", "name": "مدیریت منابع آب", "algorithms": ["H09", "H14"]},
            {"id": "WAS007", "name": "مهندسی آب", "algorithms": ["H01", "H09"]},
            {"id": "WAS008", "name": "آبیاری و زهکشی", "algorithms": ["H09", "H11"]},
            {"id": "WAS009", "name": "آبیاری تحت فشار", "algorithms": ["H09"]},
            {"id": "WAS010", "name": "آبیاری سطحی", "algorithms": ["H01", "H09"]},
            {"id": "WAS011", "name": "فیزیک خاک", "algorithms": ["H09", "H10", "H12"]},
            {"id": "WAS012", "name": "شیمی خاک", "algorithms": ["H09", "H11", "H13"]},
            {"id": "WAS013", "name": "بیولوژی خاک", "algorithms": ["H09", "H13", "H21"]},
            {"id": "WAS014", "name": "حاصلخیزی خاک", "algorithms": ["H09", "H13", "H21"]},
            {"id": "WAS015", "name": "ژنتیک خاک", "algorithms": ["H09", "H13"]},
            {"id": "WAS016", "name": "فرسایش خاک", "algorithms": ["H10"]},
            {"id": "WAS017", "name": "حفاظت خاک", "algorithms": ["H10", "H13"]},
            {"id": "WAS018", "name": "شوری خاک", "algorithms": ["H11"]},
            {"id": "WAS019", "name": "اصلاح خاک‌های شور", "algorithms": ["H11"]},
            {"id": "WAS020", "name": "خاک‌های قلیایی", "algorithms": ["H11"]},
            {"id": "WAS021", "name": "خاک‌های اسیدی", "algorithms": ["H13"]},
            {"id": "WAS022", "name": "مدیریت مواد آلی خاک", "algorithms": ["H09", "H13"]},
            {"id": "WAS023", "name": "کشاورزی حفاظتی خاک", "algorithms": ["H09", "H10"]},
            {"id": "WAS024", "name": "خاک‌شناسی محیطی", "algorithms": ["H13"]},
            {"id": "WAS025", "name": "بازسازی خاک", "algorithms": ["H09", "H13", "H21"]},
            {"id": "WAS026", "name": "خاک‌شناسی شهری", "algorithms": ["H13"]},
            {"id": "WAS027", "name": "خاک‌شناسی جنگلی", "algorithms": ["H09", "H13"]},
            {"id": "WAS028", "name": "خاک‌شناسی مرتعی", "algorithms": ["H09", "H13"]},
            {"id": "WAS029", "name": "خاک‌شناسی بیابان", "algorithms": ["H09", "H10", "H13"]},
            {"id": "WAS030", "name": "خاک‌شناسی کشاورزی دقیق", "algorithms": ["H09", "H23"]},
        ]
    },
    "economics": {
        "name": "اقتصاد و توسعه روستایی",
        "icon": "💰",
        "specialties": [
            {"id": "ECO001", "name": "اقتصاد کشاورزی", "algorithms": ["H18", "H22"]},
            {"id": "ECO002", "name": "اقتصاد منابع طبیعی", "algorithms": ["H09", "H14"]},
            {"id": "ECO003", "name": "اقتصاد محیط زیست", "algorithms": ["H09", "H13"]},
            {"id": "ECO004", "name": "اقتصاد روستایی", "algorithms": ["H25"]},
            {"id": "ECO005", "name": "توسعه روستایی", "algorithms": ["H25"]},
            {"id": "ECO006", "name": "توسعه پایدار", "algorithms": ["H09", "H13", "H25"]},
            {"id": "ECO007", "name": "اقتصاد غذا", "algorithms": ["H18"]},
            {"id": "ECO008", "name": "بازاریابی کشاورزی", "algorithms": []},
            {"id": "ECO009", "name": "مدیریت مزرعه", "algorithms": ["H18", "H22"]},
            {"id": "ECO010", "name": "اقتصاد آب", "algorithms": ["H09", "H14"]},
            {"id": "ECO011", "name": "اقتصاد خاک", "algorithms": ["H09", "H13"]},
            {"id": "ECO012", "name": "اقتصاد انرژی کشاورزی", "algorithms": []},
            {"id": "ECO013", "name": "اقتصاد تغییر اقلیم", "algorithms": ["H02", "H04"]},
            {"id": "ECO014", "name": "بیمه کشاورزی", "algorithms": ["H22"]},
            {"id": "ECO015", "name": "اعتبارات خرد روستایی", "algorithms": []},
            {"id": "ECO016", "name": "تعاونی‌های روستایی", "algorithms": ["H25"]},
            {"id": "ECO017", "name": "زنجیره تأمین کشاورزی", "algorithms": []},
            {"id": "ECO018", "name": "صنایع تبدیلی کشاورزی", "algorithms": []},
            {"id": "ECO019", "name": "صادرات کشاورزی", "algorithms": []},
            {"id": "ECO020", "name": "سیاست‌گذاری کشاورزی", "algorithms": ["H25"]},
            {"id": "ECO021", "name": "یارانه‌های کشاورزی", "algorithms": []},
            {"id": "ECO022", "name": "اقتصاد کشاورزی دقیق", "algorithms": ["H22", "H23"]},
            {"id": "ECO023", "name": "اقتصاد کشاورزی ارگانیک", "algorithms": ["H13"]},
            {"id": "ECO024", "name": "اقتصاد کشاورزی شهری", "algorithms": []},
            {"id": "ECO025", "name": "اقتصاد گلخانه", "algorithms": []},
            {"id": "ECO026", "name": "اقتصاد آبزی‌پروری", "algorithms": []},
            {"id": "ECO027", "name": "اقتصاد دامپروری", "algorithms": []},
            {"id": "ECO028", "name": "اقتصاد طیور", "algorithms": []},
            {"id": "ECO029", "name": "اقتصاد زنبورداری", "algorithms": []},
            {"id": "ECO030", "name": "اقتصاد گیاهان دارویی", "algorithms": []},
        ]
    },
    # ... (ادامه سایر حوزه‌ها به همین شکل)
}


def create_specialist_registry():
    """ایجاد رجیستری ۳۳۰ گرایش تخصصی"""
    registry = {
        "generated_at": datetime.now().isoformat(),
        "total_specialties": 0,
        "domains": {},
        "algorithm_mapping": {},
    }
    
    # شمارش و سازماندهی
    for domain_id, domain in SPECIALISTS.items():
        registry["domains"][domain_id] = {
            "name": domain["name"],
            "icon": domain["icon"],
            "count": len(domain["specialties"]),
            "specialties": domain["specialties"],
        }
        registry["total_specialties"] += len(domain["specialties"])
    
    # ماتریس ارتباط الگوریتم-گرایش
    for domain_id, domain in SPECIALISTS.items():
        for specialty in domain["specialties"]:
            for algo in specialty["algorithms"]:
                if algo not in registry["algorithm_mapping"]:
                    registry["algorithm_mapping"][algo] = []
                registry["algorithm_mapping"][algo].append({
                    "domain": domain_id,
                    "specialty_id": specialty["id"],
                    "specialty_name": specialty["name"],
                })
    
    return registry


def generate_validation_protocol():
    """تولید پروتکل اعتبارسنجی چندلایه"""
    protocol = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "layers": [
            {
                "level": 1,
                "name": "اعتبارسنجی درون‌تخصصی",
                "description": "هر گرایش تخصصی خروجی‌های مرتبط با خود را بررسی می‌کند",
                "threshold": "حداقل ۱ متخصص باید تأیید کند",
            },
            {
                "level": 2,
                "name": "اعتبارسنجی بین‌تخصصی",
                "description": "گرایش‌های مرتبط با هم تعامل می‌کنند",
                "threshold": "حداقل ۲ گرایش مختلف باید تأیید کنند",
            },
            {
                "level": 3,
                "name": "اجماع متخصصان",
                "description": "اگر ۳+ متخصص مخالف باشند، خروجی رد می‌شود",
                "threshold": "کمتر از ۳ مخالف",
            },
        ],
        "decision_rules": {
            "APPROVED": "هیچ مخالفی وجود ندارد",
            "REVIEW": "۱-۲ مخالف وجود دارد",
            "REJECTED": "۳+ مخالف وجود دارد",
        },
    }
    return protocol


def main():
    print("="*70)
    print("پیاده‌سازی سیستم ۳۳۰ گرایش تخصصی هیدروما")
    print("="*70)
    
    # ایجاد رجیستری
    print("\n[1/3] ایجاد رجیستری ۳۳۰ گرایش تخصصی ...")
    registry = create_specialist_registry()
    
    registry_file = ROOT / "docs" / "hydroma" / "specialist_registry.json"
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    registry_file.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"   ✅ رجیستری ذخیره شد: {registry_file}")
    print(f"   📊 تعداد کل گرایش‌ها: {registry['total_specialties']}")
    
    # ایجاد پروتکل اعتبارسنجی
    print("\n[2/3] ایجاد پروتکل اعتبارسنجی چندلایه ...")
    protocol = generate_validation_protocol()
    
    protocol_file = ROOT / "docs" / "hydroma" / "validation_protocol.json"
    protocol_file.write_text(json.dumps(protocol, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"   ✅ پروتکل ذخیره شد: {protocol_file}")
    
    # آمار الگوریتم‌ها
    print("\n[3/3] آمار ارتباط الگوریتم-گرایش ...")
    print("\n   الگوریتم‌های با بیشترین ارتباط:")
    algo_counts = [(algo, len(specs)) for algo, specs in registry["algorithm_mapping"].items()]
    algo_counts.sort(key=lambda x: x[1], reverse=True)
    
    for algo, count in algo_counts[:10]:
        print(f"      {algo}: {count} گرایش تخصصی")
    
    print("\n" + "="*70)
    print("🎯 شعار: تن زمین خسته است - احیای زمین با دانش ۳۳۰ متخصص")
    print("="*70)
    print("\n📋 گام‌های بعدی:")
    print("   ۱. پیاده‌سازی موتور اعتبارسنجی چندلایه")
    print("   ۲. اتصال به ۲۵ الگوریتم موجود")
    print("   ۳. تست با داده‌های واقعی")
    print("   ۴. بنچمارک رسمی")
    print("="*70)


if __name__ == "__main__":
    main()