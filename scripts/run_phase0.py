"""
Run Phase 0
===========
اجرای کامل فاز صفر با یک دستور.
"""

import sys
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
PHASE0_DIR = SCRIPTS_DIR / "phase0"

# ترتیب اجرای اسکریپت‌ها
SCRIPTS_ORDER = [
    ("check_environment.py", "بررسی پیش‌نیازها"),
    ("install_git.py", "نصب Git (در صورت نیاز)"),
    ("fix_structure.py", "رفع ساختار اشتباه پوشه‌ها"),
    ("setup_registry.py", "تنظیم رجیستری pnpm"),
    ("create_gitignore.py", "ایجاد .gitignore"),
]

def run_script(script_name: str, description: str) -> int:
    """اجرای یک اسکریپت و برگشت کد خروجی"""
    print(f"\n{'=' * 70}")
    print(f"  🎬 {description}")
    print(f"  📄 {script_name}")
    print(f"{'=' * 70}\n")
    
    script_path = PHASE0_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ فایل یافت نشد: {script_path}")
        return 1
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(SCRIPTS_DIR.parent)
    )
    
    return result.returncode

def main() -> int:
    print("\n" + "=" * 70)
    print("  🚀 اجرای کامل فاز صفر - eco_nojin")
    print("=" * 70)
    
    failed = []
    
    for script_name, description in SCRIPTS_ORDER:
        code = run_script(script_name, description)
        
        if code != 0:
            failed.append((script_name, description))
            print(f"\n⚠️ اسکریپت با خطا پایان یافت: {script_name}")
            
            response = input("\nادامه به اسکریپت بعدی؟ (y/n) [y]: ").strip().lower()
            if response not in ("", "y", "yes", "b", "بله"):
                print("❌ متوقف شد")
                break
    
    print("\n" + "=" * 70)
    print("  📊 نتیجه نهایی فاز صفر")
    print("=" * 70)
    
    if failed:
        print(f"\n❌ {len(failed)} مورد شکست خورد:")
        for name, desc in failed:
            print(f"  - {desc} ({name})")
        return 1
    
    print("\n🎉 همه مراحل با موفقیت انجام شد!")
    print("\nگام‌های بعدی:")
    print("  1. ترمینال را ببندید و باز کنید (برای PATH جدید)")
    print("  2. git --version را تست کنید")
    print("  3. cd frontend && pnpm install")
    print("  4. python scripts/phase0/init_git_repo.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())