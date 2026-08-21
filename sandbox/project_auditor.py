"""
Eco Nojin Project Auditor (Phase 0: Deep Analysis)
نویسنده: شورای عالی فنی Eco Nojin
تاریخ: 2026-08-22
هدف: تحلیل عمیق، بدون تغییر (Read-Only)، و طبقه‌بندی وضعیت دامنه‌ها بر اساس Master Specification.
"""

import os
import json
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# ==============================================================================
# 1. پیکربندی و تعاریف (Configuration & Definitions)
# ==============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.resolve() # D:\eco_nojin
REPORT_DIR = PROJECT_ROOT / "sandbox" / "audit_reports"
REPORT_DIR.mkdir(exist_ok=True)

# دامنه‌های مورد انتظار طبق Master Specification
EXPECTED_DOMAINS = [
    "soil", "climate", "hydrology", "crop", "geospatial", "satellite",
    "simulation", "scenario", "irrigation", "infrastructure", "economics", "mrv", "carbon"
]

# ماژول‌های ممنوعه در لایه موتور علمی (HyDroMa)
FORBIDDEN_IN_ENGINE = [
    "blockchain", "marketplace", "ecowallet", "ussd", "voice", "insurance", "tourism"
]

# کلمات کلیدی نشان‌دهنده کد ناقص یا شبیه‌سازی‌شده
MOCK_INDICATORS = ["pass", "raise NotImplementedError", "simulated", "mock", "todo", "placeholder"]

# ==============================================================================
# 2. موتورهای تحلیل (Analysis Engines)
# ==============================================================================

def analyze_python_file(file_path: Path) -> Dict[str, Any]:
    """تحلیل یک فایل پایتون با استفاده از AST برای تشخیص وضعیت واقعی کد"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines_of_code = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')])
        
        # بررسی وجود کدهای ناقص
        is_stub = False
        for indicator in MOCK_INDICATORS:
            if re.search(rf'\b{indicator}\b', content, re.IGNORECASE):
                is_stub = True
                break
                
        # تحلیل AST برای بررسی تعداد کلاس‌ها و توابع واقعی
        try:
            tree = ast.parse(content)
            classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        except SyntaxError:
            classes, functions = 0, 0

        return {
            "loc": lines_of_code,
            "classes": classes,
            "functions": functions,
            "is_stub_or_mock": is_stub,
            "status": "STUB/MOCK" if is_stub or lines_of_code < 20 else "PARTIAL/EXISTS"
        }
    except Exception as e:
        return {"error": str(e), "status": "BROKEN"}

def scan_directory_structure() -> Dict[str, Any]:
    """اسکن ساختار دایرکتوری و طبقه‌بندی دامنه‌ها"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "domains": {},
        "architecture_violations": [],
        "summary": {}
    }

    # بررسی دامنه‌های موتور علمی
    hydroma_path = PROJECT_ROOT / "engine" / "hydroma"
    if hydroma_path.exists():
        for item in hydroma_path.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                domain_name = item.name
                
                # 1. بررسی تخلفات معماری (وجود ماژول کسب‌وکار در موتور علمی)
                if domain_name in FORBIDDEN_IN_ENGINE:
                    report["architecture_violations"].append({
                        "type": "DOMAIN_COUPLING",
                        "location": f"engine/hydroma/{domain_name}",
                        "severity": "HIGH",
                        "description": "ماژول کسب‌وکار در لایه موتور علمی قرار دارد."
                    })

                # 2. تحلیل عمیق فایل‌های پایتون در دامنه
                py_files = list(item.rglob("*.py"))
                domain_stats = {"total_files": len(py_files), "files_detail": []}
                
                for py_file in py_files:
                    # نادیده گرفتن فایل‌های تست و کانفیگ برای آمار اصلی
                    if "test" in py_file.name or py_file.name == "__init__.py":
                        continue
                        
                    analysis = analyze_python_file(py_file)
                    domain_stats["files_detail"].append({
                        "file": str(py_file.relative_to(PROJECT_ROOT)),
                        "status": analysis["status"],
                        "loc": analysis.get("loc", 0)
                    })

                # تعیین وضعیت کلی دامنه
                stub_count = sum(1 for f in domain_stats["files_detail"] if f["status"] == "STUB/MOCK")
                total_analyzed = len(domain_stats["files_detail"])
                
                if total_analyzed == 0:
                    overall_status = "MISSING/EMPTY"
                elif stub_count == total_analyzed:
                    overall_status = "STUB/MOCK"
                elif stub_count > total_analyzed / 2:
                    overall_status = "PARTIAL (Heavy Stubbing)"
                else:
                    overall_status = "EXISTS/PARTIAL"

                report["domains"][domain_name] = {
                    "overall_status": overall_status,
                    "stats": domain_stats
                }

    # بررسی هسته C++
    cpp_path = PROJECT_ROOT / "engine" / "cpp_core"
    if cpp_path.exists():
        hpp_files = list(cpp_path.rglob("*.hpp"))
        report["domains"]["cpp_core"] = {
            "overall_status": "EXISTS" if len(hpp_files) > 0 else "MISSING",
            "header_files_count": len(hpp_files)
        }

    # خلاصه آماری
    report["summary"] = {
        "total_domains_found": len(report["domains"]),
        "violations_count": len(report["architecture_violations"]),
        "missing_expected_domains": [d for d in EXPECTED_DOMAINS if d not in report["domains"]]
    }

    return report

# ==============================================================================
# 3. تولید گزارش (Report Generation)
# ==============================================================================

def generate_markdown_report(data: Dict[str, Any]) -> str:
    """تبدیل داده‌های تحلیل به گزارش خوانا برای شورای عالی"""
    md = f"# گزارش تحلیل عمیق پروژه Eco Nojin\n"
    md += f"**تاریخ تحلیل:** {data['timestamp']}\n"
    md += f"**مسیر پروژه:** {data['project_root']}\n\n"
    
    md += "## ⚠️ تخلفات معماری شناسایی‌شده (Architecture Violations)\n"
    if data["architecture_violations"]:
        for v in data["architecture_violations"]:
            md += f"- 🔴 **{v['type']}** در `{v['location']}`: {v['description']} (Severity: {v['severity']})\n"
    else:
        md += "- ✅ هیچ تخلف معماری شدیدی شناسایی نشد.\n"
    md += "\n"

    md += "## 📊 وضعیت دامنه‌های موتور علمی (HyDroMa Domains)\n"
    md += "| دامنه (Domain) | وضعیت کلی | تعداد فایل‌های اصلی | جزئیات |\n"
    md += "|---|---|---|---|\n"
    for domain, info in data["domains"].items():
        if domain == "cpp_core":
            md += f"| **{domain}** | {info['overall_status']} | {info['header_files_count']} فایل hpp | هسته محاسباتی |\n"
        else:
            stats = info['stats']
            details = ", ".join([f"{f['file'].split('/')[-1]} ({f['status']})" for f in stats['files_detail'][:3]])
            if len(stats['files_detail']) > 3:
                details += " ..."
            md += f"| **{domain}** | `{info['overall_status']}` | {stats['total_files']} | {details} |\n"
    
    md += "\n## 🔍 دامنه‌های مورد انتظار اما یافت‌نشده (Missing Domains)\n"
    if data["summary"]["missing_expected_domains"]:
        for d in data["summary"]["missing_expected_domains"]:
            md += f"- ❌ `{d}`\n"
    else:
        md += "- ✅ تمام دامنه‌های اصلی حضور دارند.\n"

    md += "\n---\n*این گزارش توسط Eco Nojin Auditor v1.0 تولید شده است.*"
    return md

# ==============================================================================
# 4. اجرای اصلی (Main Execution)
# ==============================================================================

if __name__ == "__main__":
    print("🔍 شروع تحلیل عمیق پروژه Eco Nojin...")
    print(f"📁 مسیر هدف: {PROJECT_ROOT}")
    
    # اجرای تحلیل
    audit_data = scan_directory_structure()
    
    # تولید گزارش‌ها
    md_report = generate_markdown_report(audit_data)
    
    # ذخیره گزارش Markdown
    md_path = REPORT_DIR / "audit_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
        
    # ذخیره گزارش JSON برای پردازش‌های بعدی اسکریپت‌ها
    json_path = REPORT_DIR / "audit_data.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)
        
    print("✅ تحلیل با موفقیت به پایان رسید.")
    print(f"📄 گزارش Markdown ذخیره شد در: {md_path}")
    print(f"📦 داده‌های خام JSON ذخیره شد در: {json_path}")
    print("\n📋 خلاصه سریع:")
    print(f"   - تعداد دامنه‌های یافت‌شده: {audit_data['summary']['total_domains_found']}")
    print(f"   - تعداد تخلفات معماری: {audit_data['summary']['violations_count']}")
    print(f"   - دامنه‌های گمشده: {', '.join(audit_data['summary']['missing_expected_domains']) if audit_data['summary']['missing_expected_domains'] else 'هیچ'}")