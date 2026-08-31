#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اصلاح خطای سینتکس در اسکریپت تکمیل پایگاه دانش
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KB_SCRIPT = ROOT / "complete_knowledge_base.py"

def fix_syntax():
    print("=" * 70)
    print("اصلاح خطای سینتکس")
    print("=" * 70)
    
    if not KB_SCRIPT.exists():
        print(f"❌ فایل یافت نشد: {KB_SCRIPT}")
        return False
    
    content = KB_SCRIPT.read_text(encoding="utf-8")
    
    # خط اشتباه
    wrong_line = '"outputs": "وضعیت خشکسالی", "هشدار زودهنگام"],'
    # خط صحیح
    correct_line = '"outputs": ["وضعیت خشکسالی", "هشدار زودهنگام"],'
    
    if wrong_line in content:
        content = content.replace(wrong_line, correct_line)
        KB_SCRIPT.write_text(content, encoding="utf-8")
        print(f"✅ خطای سینتکس اصلاح شد")
        print(f"   خط اشتباه: {wrong_line}")
        print(f"   خط صحیح:   {correct_line}")
    else:
        print("⚠️ خط مورد نظر یافت نشد")
        return False
    
    print("=" * 70)
    print("\n📋 گام بعدی:")
    print("   python complete_knowledge_base.py")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    fix_syntax()