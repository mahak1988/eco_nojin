"""
Blockchain Dependencies Installer v2
هدف: نصب پکیج‌های بلاکچین بدون نیاز به کامپایل safe-pysha3
"""
import subprocess
import sys
from pathlib import Path

VENV_PIP = Path(sys.executable).parent / "Scripts" / "pip.exe"
if not VENV_PIP.exists():
    VENV_PIP = Path(sys.executable).parent / "pip.exe"

def install():
    print(f"📦 استفاده از: {VENV_PIP}")
    
    # ابتدا pycryptodome نصب شود که از قبل داریم
    packages = [
        "eth-tester==0.12.0b2",  # بدون [py-evm] در ابتدا
        "eth-account==0.13.0",
        "web3>=7.0.0",
    ]
    
    for pkg in packages:
        print(f"\n🔧 نصب: {pkg}")
        result = subprocess.run(
            [str(VENV_PIP), "install", pkg],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {pkg} نصب شد")
        else:
            print(f"⚠️ خطا: {result.stderr[-300:]}")
    
    # حالا تلاش برای نصب py-evm
    print("\n🔧 تلاش برای نصب py-evm (ممکن است نیاز به Build Tools داشته باشد)...")
    result = subprocess.run(
        [str(VENV_PIP), "install", "py-evm>=0.10.0b0"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ py-evm نصب شد")
    else:
        print("⚠️ py-evm نصب نشد - تست‌های Web3 ممکن است skip شوند")
        print("   (این برای فازهای بعدی بلاکچین حل خواهد شد)")

if __name__ == "__main__":
    install()