#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch: رفع SyntaxError در f-string
═══════════════════════════════════════════════════════════════════════
تابع generate_report را با نسخه safe جایگزین می‌کند.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")
TARGET_FILE = PROJECT_ROOT / "phase3_complete_priority_modules.py"


def patch():
    print("=" * 70)
    print("  Patching phase3_complete_priority_modules.py")
    print("=" * 70)
    
    if not TARGET_FILE.exists():
        print(f"  [X] فایل یافت نشد: {TARGET_FILE}")
        return False
    
    content = TARGET_FILE.read_text(encoding='utf-8')
    
    # پیدا کردن تابع generate_report و جایگزینی آن
    # الگو: از def generate_report تا اولین def بعدی یا انتهای فایل
    
    new_generate_report = '''def generate_report(results: Dict[str, bool]):
    separator("تولید گزارش نهایی")
    
    all_passed = all(results.values())
    
    # استفاده از string معمولی به جای f-string برای جلوگیری از SyntaxError
    report_parts = []
    
    report_parts.append("# 📊 گزارش فاز ۳ - موج ۱\\n\\n")
    report_parts.append(f"**تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
    
    report_parts.append("## ماژول‌های تکمیل‌شده\\n\\n")
    report_parts.append("| ماژول | Priority | وضعیت |\\n")
    report_parts.append("|---|---|---|\\n")
    report_parts.append("| analytics | 10/10 | ✅ کامل |\\n")
    report_parts.append("| auth | 9/10 | ✅ کامل |\\n")
    report_parts.append("| admin | 8/10 | ✅ کامل |\\n")
    report_parts.append("| reporting | 8/10 | ✅ کامل |\\n\\n")
    
    report_parts.append("## ساختار هر ماژول\\n\\n")
    report_parts.append("```\\n")
    report_parts.append("services/X/\\n")
    report_parts.append("├── __init__.py          # Exports\\n")
    report_parts.append("├── models.py            # SQLAlchemy models\\n")
    report_parts.append("├── schemas.py           # Pydantic schemas\\n")
    report_parts.append("├── service.py           # Business logic\\n")
    report_parts.append("├── repository.py        # Data access\\n")
    report_parts.append("├── api/\\n")
    report_parts.append("│   └── __init__.py      # FastAPI router\\n")
    report_parts.append("└── tests/\\n")
    report_parts.append("    └── test_integration.py\\n")
    report_parts.append("```\\n\\n")
    
    report_parts.append("## API Endpoints جدید\\n\\n")
    
    report_parts.append("### Analytics\\n")
    report_parts.append("- `GET /analytics/dashboard`\\n")
    report_parts.append("- `GET /analytics/sales-summary`\\n")
    report_parts.append("- `GET /analytics/tourism-metrics`\\n")
    report_parts.append("- `GET /analytics/landscape-metrics`\\n\\n")
    
    report_parts.append("### Auth\\n")
    report_parts.append("- `POST /auth/register`\\n")
    report_parts.append("- `POST /auth/login`\\n")
    report_parts.append("- `POST /auth/refresh`\\n\\n")
    
    report_parts.append("### Admin\\n")
    report_parts.append("- `GET /admin/health`\\n")
    report_parts.append("- `GET /admin/status`\\n")
    report_parts.append("- `GET /admin/inventory`\\n")
    report_parts.append("- `GET /admin/stats`\\n")
    report_parts.append("- `GET /admin/audit-logs`\\n\\n")
    
    report_parts.append("### Reporting\\n")
    report_parts.append("- `POST /reports/`\\n")
    report_parts.append("- `POST /reports/<id>/generate`\\n")
    report_parts.append("- `GET /reports/<id>`\\n")
    report_parts.append("- `GET /reports/`\\n\\n")
    
    report_parts.append("## نتایج تست‌ها\\n\\n")
    
    for test_file, passed in results.items():
        icon = "✅" if passed else "❌"
        report_parts.append(f"- {icon} `{test_file}`\\n")
    
    status = "موفق" if all_passed else "ناموفق"
    report_parts.append(f"\\n**وضعیت نهایی:** {status}\\n\\n")
    
    if all_passed:
        report_parts.append("## 🚀 گام‌های بعدی\\n\\n")
        report_parts.append("### Commit:\\n")
        report_parts.append("```bash\\n")
        report_parts.append("git add -A\\n")
        report_parts.append("git commit -m \\"phase3-wave1: complete priority skeleton modules\\"\\n")
        report_parts.append("```\\n\\n")
        
        report_parts.append("### فاز ۳ - موج ۲ (اختیاری):\\n")
        report_parts.append("- `bots` (Priority 7)\\n")
        report_parts.append("- `satellite` (Priority 7)\\n")
        report_parts.append("- `map_engine` (Priority 6)\\n")
        report_parts.append("- `telegram_bot` (Priority 6)\\n\\n")
        
        report_parts.append("### فاز ۳ - موج ۳:\\n")
        report_parts.append("- `carbon` (Priority 5) - بهبود\\n")
    
    report = "".join(report_parts)
    
    report_file = PROJECT_ROOT / "PHASE3_WAVE1_REPORT.md"
    report_file.write_text(report, encoding='utf-8')
    log(f"گزارش: {report_file}", "+")
    
    return all_passed

'''
    
    # پیدا کردن و جایگزینی تابع generate_report
    # الگو: از "def generate_report" تا "def " بعدی (main)
    
    pattern = r'def generate_report\(results: Dict\[str, bool\]\):.*?(?=\n# ═|\ndef main\(\):)'
    
    new_content, count = re.subn(
        pattern,
        new_generate_report.rstrip() + "\n\n\n",
        content,
        flags=re.DOTALL
    )
    
    if count == 0:
        print("  [!] الگو پیدا نشد - تلاش با روش جایگزین")
        # روش جایگزین: پیدا کردن خط def generate_report و جایگزینی تا خط بعدی def
        lines = content.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if line.startswith('def generate_report('):
                start_idx = i
            elif start_idx is not None and line.startswith('def '):
                end_idx = i
                break
        
        if start_idx is not None:
            if end_idx is None:
                end_idx = len(lines)
            
            # جایگزینی
            new_lines = lines[:start_idx] + new_generate_report.split('\n') + [''] + lines[end_idx:]
            new_content = '\n'.join(new_lines)
            count = 1
    
    if count > 0:
        TARGET_FILE.write_text(new_content, encoding='utf-8')
        print(f"  [+] تابع generate_report با موفقیت جایگزین شد")
        print(f"  [+] فایل ذخیره شد: {TARGET_FILE}")
        return True
    else:
        print("  [X] جایگزینی ناموفق بود")
        return False


if __name__ == "__main__":
    success = patch()
    exit(0 if success else 1)