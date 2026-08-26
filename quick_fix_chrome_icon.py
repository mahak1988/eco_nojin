#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""رفع سریع خطای Chrome icon"""

from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")

def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

def fix_login_page():
    """رفع خطای Chrome import در LoginPage"""
    print("\n" + "=" * 70)
    print("  🔧 رفع خطای Chrome icon")
    print("=" * 70 + "\n")
    
    login_path = FRONTEND_ROOT / 'src' / 'pages' / 'LoginPage.tsx'
    
    if not login_path.exists():
        log("LoginPage.tsx یافت نشد!", "X")
        return False
    
    content = login_path.read_text(encoding='utf-8')
    
    # بررسی اینکه Chrome وجود دارد
    if 'Chrome' not in content:
        log("Chrome در فایل نیست - مشکلی وجود ندارد", "✓")
        return True
    
    # حذف Chrome از import
    content = content.replace('Chrome,', '')
    content = content.replace(', Chrome', '')
    content = content.replace('Chrome }', '}')
    
    # حذف استفاده از Chrome در کد
    content = content.replace('<Chrome', '<Globe')
    content = content.replace('Chrome />', 'Globe />')
    content = content.replace('Chrome size=', 'Globe size=')
    
    # اطمینان از وجود Globe در import
    if 'Globe' not in content and "from 'lucide-react'" in content:
        content = content.replace(
            "} from 'lucide-react';",
            "Globe,\n} from 'lucide-react';"
        )
    
    write_file(login_path, content)
    log("LoginPage.tsx اصلاح شد", "+")
    
    # همچنین RegisterPage و ForgotPassword
    for page_name in ['RegisterPage.tsx', 'ForgotPasswordPage.tsx']:
        page_path = FRONTEND_ROOT / 'src' / 'pages' / page_name
        if page_path.exists():
            content = page_path.read_text(encoding='utf-8')
            if 'Chrome' in content:
                content = content.replace('Chrome,', '').replace(', Chrome', '')
                content = content.replace('Chrome }', '}')
                content = content.replace('<Chrome', '<Globe')
                write_file(page_path, content)
                log(f"{page_name} اصلاح شد", "+")
    
    return True

def main():
    if fix_login_page():
        print("\n" + "=" * 70)
        print("  ✅ رفع شد!")
        print("=" * 70)
        print("\n  🚀 اجرا:")
        print("     cd frontend")
        print("     pnpm run dev")
        print("\n  ⚠️  درباره هشدارهای MetaMask:")
        print("     آن هشدارها از browser extension هستند، نه از کد شما.")
        print("     می‌توانید آنها را نادیده بگیرید.")
        return 0
    return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())