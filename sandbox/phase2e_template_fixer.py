"""
Phase 2e: Template Fixer
هدف: اصلاح template generator برای فازهای آینده
تغییر: جلوگیری از try بلوک خالی
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
GENERATOR = PROJECT_ROOT / "sandbox" / "phase2d_bridge_connector.py"


def fix_template():
    """اصلاح تابع generate_bridge_file_v2 برای مدیریت pre_convert خالی"""
    
    if not GENERATOR.exists():
        print(f"❌ فایل یافت نشد: {GENERATOR}")
        return
    
    content = GENERATOR.read_text(encoding="utf-8")
    
    # الگوی قدیمی (مشکل‌ساز)
    old_pattern = '''        try:
{pre_lines}
{func["cxx_call"]}'''
    
    # الگوی جدید (ایمن)
    new_pattern = '''        try:
{pre_lines_or_pass}
{func["cxx_call"]}'''
    
    if old_pattern not in content:
        print("⚠️ الگوی قدیمی یافت نشد. احتمالاً از قبل اصلاح شده.")
        return
    
    # اصلاح template string
    content = content.replace(old_pattern, new_pattern)
    
    # اضافه کردن محاسبه pre_lines_or_pass
    old_pre_calc = 'pre_lines = "\\n".join(func["pre_convert"]) if func["pre_convert"] else ""'
    new_pre_calc = '''pre_lines = "\\n".join(func["pre_convert"]) if func["pre_convert"] else ""
        pre_lines_or_pass = pre_lines if pre_lines.strip() else "            pass  # No pre-conversion needed"'''
    
    content = content.replace(old_pre_calc, new_pre_calc)
    
    GENERATOR.write_text(content, encoding="utf-8")
    print(f"✅ Template generator اصلاح شد: {GENERATOR.name}")
    
    # اعتبارسنجی
    import ast
    try:
        ast.parse(content)
        print("✅ فایل generator از نظر نحوی سالم است.")
    except SyntaxError as e:
        print(f"❌ خطای نحوی در generator: {e}")


if __name__ == "__main__":
    fix_template()