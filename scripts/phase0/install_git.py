"""
Install Git
===========
نصب خودکار Git روی Windows.
"""

import sys
import urllib.request
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import console, shell

GIT_INSTALLER_URL = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe"

def check_if_installed() -> bool:
    """بررسی اینکه آیا Git قبلاً نصب شده"""
    if shell.command_exists("git"):
        code, out, _ = shell.run("git --version", silent=True)
        if code == 0:
            console.success(f"Git قبلاً نصب است: {out.strip()}")
            return True
    return False

def download_installer(dest: Path) -> bool:
    """دانلود نصب‌کننده Git"""
    console.info(f"دانلود Git از: {GIT_INSTALLER_URL}")
    console.info("این ممکن است چند دقیقه طول بکشد...")
    
    try:
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                print(f"\r  📥 {percent:5.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
        
        urllib.request.urlretrieve(GIT_INSTALLER_URL, dest, reporthook=report_progress)
        print()  # خط جدید
        console.success(f"دانلود کامل شد: {dest}")
        return True
    except Exception as e:
        console.error(f"خطا در دانلود: {e}")
        return False

def install_git_silent(installer: Path) -> bool:
    """نصب Git به صورت silent"""
    console.info("نصب Git در حال انجام است (چند دقیقه)...")
    
    # Silent install options
    # /VERYSILENT - بدون UI
    # /NORESTART - بدون ری‌استارت
    # /COMPONENTS - انتخاب کامپوننت‌ها
    cmd = (
        f'"{installer}" /VERYSILENT /NORESTART /NOCANCEL /SP- '
        f'/CLOSEAPPLICATIONS /RESTARTAPPLICATIONS '
        f'/COMPONENTS="icons,ext\\reg\\shellhere,assoc,assoc_sh"'
    )
    
    try:
        code, _, _ = shell.run(cmd, check=False, silent=True)
        if code == 0:
            console.success("نصب Git کامل شد")
            return True
        else:
            console.error(f"نصب با کد {code} پایان یافت")
            return False
    except Exception as e:
        console.error(f"خطا در نصب: {e}")
        return False

def refresh_path() -> None:
    """بارگذاری مجدد PATH در session فعلی"""
    import os
    
    # خواندن PATH از registry
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
        machine_path, _ = winreg.QueryValueEx(key, "Path")
        winreg.CloseKey(key)
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        user_path, _ = winreg.QueryValueEx(key, "Path")
        winreg.CloseKey(key)
        
        new_path = f"{machine_path};{user_path}"
        os.environ["PATH"] = new_path
        console.success("PATH به‌روز شد")
    except Exception as e:
        console.warning(f"به‌روزرسانی PATH خودکار ناموفق: {e}")
        console.info("💡 ممکن است نیاز به باز کردن ترمینال جدید داشته باشید")

def verify_installation() -> bool:
    """تأیید نصب"""
    refresh_path()
    
    if shell.command_exists("git"):
        code, out, _ = shell.run("git --version", silent=True)
        if code == 0:
            console.success(f"تأیید نصب: {out.strip()}")
            return True
    
    console.error("Git پس از نصب یافت نشد")
    console.info("💡 احتمالاً نیاز است ترمینال را ببندید و دوباره باز کنید")
    return False

def main() -> int:
    console.header("🔧 نصب خودکار Git برای Windows")
    
    if check_if_installed():
        return 0
    
    if sys.platform != "win32":
        console.error("این اسکریپت فقط برای Windows است")
        console.info("💡 برای Linux/Mac از package manager استفاده کنید")
        return 1
    
    # تأیید از کاربر
    response = console.question(
        "آیا Git نصب شود؟ (نیاز به دسترسی Administrator)",
        default="y"
    )
    
    if response.lower() not in ("y", "yes", "b", "بله"):
        console.warning("لغو شد")
        return 0
    
    # دانلود
    with tempfile.TemporaryDirectory() as tmpdir:
        installer = Path(tmpdir) / "Git-Installer.exe"
        
        if not download_installer(installer):
            console.error("دانلود ناموفق بود")
            console.info("💡 نصب دستی: https://git-scm.com/download/win")
            return 1
        
        # نصب
        if not install_git_silent(installer):
            console.error("نصب ناموفق بود")
            console.info("💡 نصب دستی: روی فایل exe دوبار کلیک کنید")
            return 1
    
    # تأیید
    if verify_installation():
        console.success("\n🎉 Git با موفقیت نصب شد!")
        console.info("💡 در همین ترمینال، git کار می‌کند")
        return 0
    else:
        console.warning("\n⚠️ Git نصب شد اما در این session یافت نمی‌شود")
        console.info("💡 ترمینال را ببندید و دوباره باز کنید")
        return 0

if __name__ == "__main__":
    sys.exit(main())