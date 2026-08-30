"""
Check Environment
=================
بررسی همه پیش‌نیازهای فاز صفر.
"""

import sys
import shutil
from pathlib import Path

# افزودن scripts به path برای import
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import console, shell

def check_python() -> bool:
    console.step(1, "بررسی Python")
    version = sys.version_info
    console.info(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        console.error("Python 3.10 یا بالاتر نیاز است")
        return False
    
    console.success(f"Python {version.major}.{version.minor} مناسب است")
    return True

def check_node() -> bool:
    console.step(2, "بررسی Node.js")
    
    if not shell.command_exists("node"):
        console.error("Node.js نصب نیست")
        console.info("💡 دانلود از: https://nodejs.org/en/download/")
        return False
    
    code, out, _ = shell.run("node --version", silent=True)
    if code == 0:
        console.success(f"Node.js {out.strip()} نصب است")
        return True
    
    console.error("خطا در دریافت نسخه Node.js")
    return False

def check_pnpm() -> bool:
    console.step(3, "بررسی pnpm")
    
    if not shell.command_exists("pnpm"):
        console.error("pnpm نصب نیست")
        console.info("💡 نصب: npm install -g pnpm")
        return False
    
    code, out, _ = shell.run("pnpm --version", silent=True)
    if code == 0:
        console.success(f"pnpm {out.strip()} نصب است")
        return True
    
    return False

def check_git() -> bool:
    console.step(4, "بررسی Git")
    
    if not shell.command_exists("git"):
        console.warning("Git نصب نیست - لازم است نصب شود")
        console.info("💡 پس از اجرای install_git.py، Git نصب می‌شود")
        return False
    
    code, out, _ = shell.run("git --version", silent=True)
    if code == 0:
        console.success(f"{out.strip()} نصب است")
        return True
    
    return False

def check_project_structure() -> bool:
    console.step(5, "بررسی ساختار پروژه")
    
    project_root = Path(__file__).parent.parent.parent
    required = [
        "frontend",
        "engine",
        "services",
    ]
    
    all_ok = True
    for folder in required:
        path = project_root / folder
        if path.exists() and path.is_dir():
            console.success(f"✓ {folder}/")
        else:
            console.error(f"✗ {folder}/ یافت نشد")
            all_ok = False
    
    return all_ok

def check_frontend() -> bool:
    console.step(6, "بررسی پوشه frontend")
    
    project_root = Path(__file__).parent.parent.parent
    frontend = project_root / "frontend"
    
    required_files = [
        "package.json",
        "vite.config.ts",
        "tsconfig.json",
    ]
    
    all_ok = True
    for f in required_files:
        path = frontend / f
        if path.exists():
            console.success(f"✓ {f}")
        else:
            console.error(f"✗ {f} یافت نشد")
            all_ok = False
    
    return all_ok

def main() -> int:
    console.header("🔍 بررسی محیط پروژه eco_nojin")
    
    checks = [
        ("Python", check_python()),
        ("Node.js", check_node()),
        ("pnpm", check_pnpm()),
        ("Git", check_git()),
        ("Project Structure", check_project_structure()),
        ("Frontend", check_frontend()),
    ]
    
    console.header("📊 نتیجه بررسی")
    
    failed = [name for name, ok in checks if not ok]
    
    for name, ok in checks:
        status = "✓" if ok else "✗"
        color = "🟢" if ok else "🔴"
        print(f"  {color} {name}")
    
    if failed:
        console.error(f"\n{len(failed)} مورد نیاز به رفع دارد:")
        for f in failed:
            print(f"    - {f}")
        return 1
    
    console.success("\n✨ همه پیش‌نیازها آماده هستند!")
    return 0

if __name__ == "__main__":
    sys.exit(main())