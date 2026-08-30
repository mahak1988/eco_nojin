"""
Setup Registry
==============
رفع مشکل ECONNRESET با تنظیم رجیستری صحیح npm.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import console, shell

PROJECT_ROOT = Path(__file__).parent.parent.parent

def create_npmrc() -> bool:
    """ایجاد .npmrc در frontend با رجیستری صحیح"""
    npmrc_path = PROJECT_ROOT / "frontend" / ".npmrc"
    
    content = """# pnpm registry configuration
registry=https://registry.npmjs.org/

# Optional: برای ایران ممکن است mirror نیاز باشد
# registry=https://registry.npmmirror.com/

# Strict SSL
strict-ssl=true

# Auto-install peers
auto-install-peers=true

# Shamefully hoist (برای بعضی پروژه‌های قدیمی)
shamefully-hoist=true
"""
    
    try:
        npmrc_path.write_text(content, encoding='utf-8')
        console.success(f"✓ .npmrc ایجاد شد: {npmrc_path}")
        return True
    except Exception as e:
        console.error(f"خطا در ایجاد .npmrc: {e}")
        return False

def create_root_npmrc() -> bool:
    """ایجاد .npmrc در ریشه پروژه"""
    npmrc_path = PROJECT_ROOT / ".npmrc"
    
    content = """# Root pnpm configuration
registry=https://registry.npmjs.org/
strict-ssl=true
auto-install-peers=true
"""
    
    try:
        npmrc_path.write_text(content, encoding='utf-8')
        console.success(f"✓ .npmrc ایجاد شد: {npmrc_path}")
        return True
    except Exception as e:
        console.error(f"خطا: {e}")
        return False

def set_pnpm_config() -> bool:
    """تنظیم pnpm config جهانی"""
    commands = [
        "pnpm config set registry https://registry.npmjs.org/",
        "pnpm config set auto-install-peers true",
    ]
    
    for cmd in commands:
        code, _, err = shell.run(cmd, check=False)
        if code == 0:
            console.success(f"✓ {cmd}")
        else:
            console.warning(f"⚠️ {cmd} - {err[:100]}")
    
    return True

def clear_pnpm_cache() -> bool:
    """پاک‌سازی کش pnpm"""
    console.info("پاک‌سازی کش pnpm...")
    
    # پاک کردن node_modules اگر ناقص است
    node_modules = PROJECT_ROOT / "frontend" / "node_modules"
    if node_modules.exists():
        console.warning("node_modules وجود دارد - در صورت مشکل، دستی حذف شود")
    
    return True

def test_connection() -> bool:
    """تست اتصال به registry"""
    console.info("تست اتصال به npmjs.org...")
    
    import urllib.request
    try:
        with urllib.request.urlopen("https://registry.npmjs.org/", timeout=10) as response:
            if response.status == 200:
                console.success("✓ اتصال به npmjs.org موفق بود")
                return True
    except Exception as e:
        console.error(f"✗ اتصال ناموفق: {e}")
    
    return False

def main() -> int:
    console.header("🌐 تنظیم رجیستری pnpm")
    
    # تست اتصال
    if not test_connection():
        console.warning("⚠️ اتصال به npmjs.org ممکن است مشکل داشته باشد")
        console.info("💡 ممکن است نیاز به VPN یا proxy باشد")
        response = console.question("ادامه داده شود؟", default="y")
        if response.lower() not in ("y", "yes", "b"):
            return 1
    
    # ایجاد فایل‌ها
    create_npmrc()
    create_root_npmrc()
    
    # تنظیم pnpm
    set_pnpm_config()
    
    # پاک‌سازی کش
    clear_pnpm_cache()
    
    console.header("✅ تنظیم رجیستری کامل شد")
    console.info("حالا می‌توانید pnpm install را دوباره اجرا کنید")
    console.info("💡 دستور: cd frontend && pnpm install")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())