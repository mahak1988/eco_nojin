"""
Blockchain Dependencies Installer
هدف: نصب پکیج‌های بلاکچین با مدیریت دقیق خطاها
"""
import subprocess
import sys
from pathlib import Path

VENV_PIP = Path(sys.executable).parent / "Scripts" / "pip.exe"
if not VENV_PIP.exists():
    VENV_PIP = Path(sys.executable).parent / "pip.exe"  # Linux/Mac

def install():
    if not VENV_PIP.exists():
        print(f"❌ pip یافت نشد در: {VENV_PIP}")
        return
    
    print(f"📦 استفاده از pip: {VENV_PIP}")
    
    packages = [
        "eth-tester[py-evm]==0.12.0b2",
        "eth-account==0.13.0",
        "py-evm>=0.10.0b2"
    ]
    
    for pkg in packages:
        print(f"\n🔧 در حال نصب: {pkg}")
        result = subprocess.run(
            [str(VENV_PIP), "install", pkg, "--no-deps"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {pkg} با موفقیت نصب شد.")
        else:
            print(f"⚠️ خطا در نصب {pkg}:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    
    # نصب کامل در انتها
    print("\n🔧 نصب کامل با وابستگی‌ها...")
    subprocess.run([str(VENV_PIP), "install", "eth-tester[py-evm]"])
    print("✅ عملیات نصب به پایان رسید.")

if __name__ == "__main__":
    install()