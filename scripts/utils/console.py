"""
Console Utilities
=================
ابزارهای لاگ و نمایش رنگی در کنسول.
"""

import sys
from typing import Optional

class Colors:
    """کدهای رنگ ANSI برای کنسول"""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

# فعال‌سازی رنگ در Windows
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def info(msg: str) -> None:
    """پیام اطلاعاتی آبی"""
    print(f"{Colors.BLUE}ℹ{Colors.RESET}  {msg}")

def success(msg: str) -> None:
    """پیام موفقیت سبز"""
    print(f"{Colors.GREEN}✓{Colors.RESET}  {msg}")

def warning(msg: str) -> None:
    """پیام هشدار زرد"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET}  {msg}")

def error(msg: str) -> None:
    """پیام خطای قرمز"""
    print(f"{Colors.RED}✗{Colors.RESET}  {msg}")

def header(msg: str) -> None:
    """تیتر با استایل"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}\n")

def step(number: int, msg: str) -> None:
    """گام اجرایی"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}[گام {number}]{Colors.RESET} {msg}")
    print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")

def question(msg: str, default: Optional[str] = None) -> str:
    """پرسش از کاربر"""
    suffix = f" [{default}]" if default else ""
    response = input(f"{Colors.CYAN}?{Colors.RESET}  {msg}{suffix}: ").strip()
    return response or default or ""