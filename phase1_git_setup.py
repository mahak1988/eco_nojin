"""
Phase 1.4: Git Smart Setup (Auto-finds Git on Windows)
"""
import subprocess
import os
import shutil

def find_git_path():
    # اول چک میکند آیا git در متغیرهای محیطی هست
    git_cmd = shutil.which('git')
    if git_cmd:
        return 'git'
    
    # اگر نبود، مسیرهای پیش‌فرض نصب در ویندوز را بررسی می‌کند
    common_paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"[INFO] Found Git manually at: {path}")
            return f'"{path}"'
            
    return None

def run_command(cmd, check=True):
    # در ویندوز برای دستورات دارای مسیر فضای خالی، از shell=True استفاده میکنیم
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"[ERROR] Command failed: {cmd}\n{result.stderr}")
        return False
    return result.stdout.strip()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # پیدا کردن گیت
    git_cmd = find_git_path()
    if not git_cmd:
        print("[FATAL ERROR] Git is not installed or not in system PATH.")
        print("[ACTION] Please download and install Git from: https://git-scm.com/download/win")
        print("[ACTION] During installation, MAKE SURE to check 'Git from the command line and also from 3rd-party software'")
        return

    # ۱. مقداردهی اولیه
    if not os.path.exists(".git"):
        print("[ACTION] Initializing Git repository...")
        run_command(f"{git_cmd} init")
        print("[SUCCESS] Git initialized.")
    else:
        print("[INFO] Git repository already exists. Skipping init.")

    # ۲. افزودن فایل‌ها
    print("[ACTION] Staging files (respecting .gitignore)...")
    if not run_command(f"{git_cmd} add ."):
        return

    # ۳. بررسی وضعیت
    status = run_command(f"{git_cmd} status --short")
    if not status:
        print("[INFO] Nothing to commit. Working tree clean.")
        return

    lines_count = len(status.splitlines())
    print(f"[INFO] Staged {lines_count} items. (Ignoring heavy files via .gitignore)")

    # ۴. ایجاد اولین کامیت
    commit_msg = "chore: phase 1 stabilization - remove 4600+ prints, update gitignore"
    print(f"[ACTION] Creating commit...")
    
    if run_command(f'{git_cmd} commit -m "{commit_msg}"'):
        print("\n" + "="*50)
        print("[SUCCESS] PHASE 1 COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("Your 220k+ LOC project is now safe and tracked by Git.")
    else:
        print("[WARN] Commit failed. Check if git config user.name and user.email are set.")
        print("[ACTION] Run these commands if needed:")
        print(f'   {git_cmd} config --global user.name "Your Name"')
        print(f'   {git_cmd} config --global user.email "your.email@example.com"')

if __name__ == "__main__":
    main()