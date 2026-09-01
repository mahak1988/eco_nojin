"""
Run Phase 0
===========
اجرای کامل فاز صفر با یک دستور.
"""

import structlog

logger = structlog.get_logger()
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
    logger.info(f"\n{'=' * 70}")
    logger.info(f"  🎬 {description}")
    logger.info(f"  📄 {script_name}")
    logger.info(f"{'=' * 70}\n")
    
    script_path = PHASE0_DIR / script_name
    
    if not script_path.exists():
        logger.info(f"❌ فایل یافت نشد: {script_path}")
        return 1
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(SCRIPTS_DIR.parent)
    )
    
    return result.returncode

def main() -> int:
    logger.info("\n" + "=" * 70)
    logger.info("  🚀 اجرای کامل فاز صفر - eco_nojin")
    logger.info("=" * 70)
    
    failed = []
    
    for script_name, description in SCRIPTS_ORDER:
        code = run_script(script_name, description)
        
        if code != 0:
            failed.append((script_name, description))
            logger.info(f"\n⚠️ اسکریپت با خطا پایان یافت: {script_name}")
            
            response = input("\nادامه به اسکریپت بعدی؟ (y/n) [y]: ").strip().lower()
            if response not in ("", "y", "yes", "b", "بله"):
                logger.info("❌ متوقف شد")
                break
    
    logger.info("\n" + "=" * 70)
    logger.info("  📊 نتیجه نهایی فاز صفر")
    logger.info("=" * 70)
    
    if failed:
        logger.info(f"\n❌ {len(failed)} مورد شکست خورد:")
        for name, desc in failed:
            logger.info(f"  - {desc} ({name})")
        return 1
    
    logger.info("\n🎉 همه مراحل با موفقیت انجام شد!")
    logger.info("\nگام‌های بعدی:")
    logger.info("  1. ترمینال را ببندید و باز کنید (برای PATH جدید)")
    logger.info("  2. git --version را تست کنید")
    logger.info("  3. cd frontend && pnpm install")
    logger.info("  4. python scripts/phase0/init_git_repo.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())