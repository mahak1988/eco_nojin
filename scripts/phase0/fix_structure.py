"""
Fix Structure
=============
رفع مشکل ساختار اشتباه پوشه‌ها:
frontend/frontend/src/ → frontend/src/
"""

import structlog

logger = structlog.get_logger()
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import console

PROJECT_ROOT = Path(__file__).parent.parent.parent

def find_wrong_structure() -> list:
    """پیدا کردن ساختارهای اشتباه ایجاد شده"""
    wrong_paths = []
    
    # الگوی اشتباه: frontend/frontend/...
    double_frontend = PROJECT_ROOT / "frontend" / "frontend"
    if double_frontend.exists():
        wrong_paths.append(double_frontend)
    
    return wrong_paths

def move_wrong_structure(wrong_path: Path) -> bool:
    """انتقال محتوای اشتباه به محل درست"""
    console.info(f"بررسی: {wrong_path}")
    
    # محتوای اشتباه (مثلاً src, features) باید به frontend/ منتقل شود
    correct_base = PROJECT_ROOT / "frontend"
    
    moved_count = 0
    for item in wrong_path.iterdir():
        src = item
        dst = correct_base / item.name
        
        if dst.exists():
            console.warning(f"  ⚠️ مقصد وجود دارد: {dst.name} - ادغام می‌شود")
            
            if dst.is_dir() and src.is_dir():
                # ادغام پوشه‌ها
                for sub in src.iterdir():
                    sub_dst = dst / sub.name
                    if not sub_dst.exists():
                        shutil.move(str(sub), str(sub_dst))
                        console.success(f"    ✓ {sub.name} ادغام شد")
                # حذف پوشه خالی
                try:
                    src.rmdir()
                except OSError:
                    pass
        else:
            shutil.move(str(src), str(dst))
            console.success(f"  ✓ {item.name} منتقل شد به {correct_base}")
            moved_count += 1
    
    # حذف پوشه خالی اشتباه
    try:
        if not any(wrong_path.iterdir()):
            wrong_path.rmdir()
            console.success(f"  ✓ پوشه خالی حذف شد: {wrong_path.name}")
    except OSError as e:
        console.warning(f"  ⚠️ حذف پوشه خالی ناموفق: {e}")
    
    return moved_count > 0

def clean_double_frontend() -> bool:
    """پاک‌سازی کامل frontend/frontend/"""
    double = PROJECT_ROOT / "frontend" / "frontend"
    
    if not double.exists():
        console.success("ساختار اشتباه یافت نشد (تمیز است)")
        return True
    
    console.warning(f"ساختار اشتباه پیدا شد: {double}")
    
    # بررسی محتوا
    items = list(double.iterdir())
    console.info(f"تعداد آیتم‌ها: {len(items)}")
    
    for item in items:
        console.info(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
    
    response = console.question("آیا منتقل و پاک‌سازی شود؟", default="y")
    
    if response.lower() not in ("y", "yes", "b", "بله"):
        console.warning("لغو شد")
        return False
    
    # انتقال محتوا
    move_wrong_structure(double)
    
    # حذف نهایی اگر خالی شد
    if double.exists() and not any(double.iterdir()):
        double.rmdir()
        console.success(f"✓ پوشه اشتباه کاملاً حذف شد: {double}")
    
    return True

def verify_structure() -> bool:
    """تأیید ساختار نهایی"""
    console.header("📋 ساختار فعلی frontend/")
    
    frontend = PROJECT_ROOT / "frontend"
    if not frontend.exists():
        console.error("frontend/ یافت نشد")
        return False
    
    items = sorted(frontend.iterdir())
    for item in items:
        icon = "📁" if item.is_dir() else "📄"
        logger.info(f"  {icon} {item.name}")
    
    # بررسی وجود src
    src = frontend / "src"
    if src.exists():
        console.success("✓ frontend/src/ وجود دارد")
    else:
        console.error("✗ frontend/src/ یافت نشد")
        return False
    
    return True

def main() -> int:
    console.header("🔨 رفع ساختار اشتباه پوشه‌ها")
    
    if not clean_double_frontend():
        return 1
    
    if verify_structure():
        console.success("\n✨ ساختار صحیح است!")
        return 0
    
    console.error("\n❌ ساختار همچنان مشکل دارد")
    return 1

if __name__ == "__main__":
    sys.exit(main())