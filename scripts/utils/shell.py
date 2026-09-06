"""
Shell Utilities
===============
اجرای دستورات shell با مدیریت خطا و لاگ.
"""

import structlog

logger = structlog.get_logger()
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
from . import console

_CMD_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")

def run(
    cmd: str,
    cwd: Optional[Path] = None,
    check: bool = True,
    capture: bool = True,
    silent: bool = False,
) -> Tuple[int, str, str]:
    """
    اجرای دستور shell.
    
    Args:
        cmd: دستور به صورت string
        cwd: پوشه کاری
        check: اگر True، در صورت خطا Exception می‌دهد
        capture: گرفتن stdout و stderr
        silent: عدم چاپ خروجی
        
    Returns:
        (return_code, stdout, stderr)
    """
    if not silent:
        console.info(f"اجرای دستور: {cmd}")
    
    try:
        result = subprocess.run(cmd.split() if isinstance(cmd, str) else cmd, shell=False, cwd=cwd,
            capture_output=capture,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if capture and not silent:
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:20]:
                    logger.info(f"  {line}")
            if result.returncode != 0 and result.stderr:
                console.error(f"stderr: {result.stderr[:500]}")
        
        if check and result.returncode != 0:
            raise RuntimeError(
                f"دستور با کد {result.returncode} شکست خورد: {cmd}\n"
                f"stderr: {result.stderr}"
            )
        
        return result.returncode, result.stdout, result.stderr
        
    except FileNotFoundError as e:
        console.error(f"دستور پیدا نشد: {e}")
        if check:
            raise
        return 1, "", str(e)

def command_exists(cmd: str) -> bool:
    """بررسی وجود یک دستور در سیستم"""
    if not _CMD_RE.match(cmd):
        raise ValueError("Invalid command name: %r" % (cmd,))
    if sys.platform == "win32":
        check_cmd = "where " + cmd
    else:
        check_cmd = "which " + cmd
    code, _, _ = run(check_cmd, check=False, silent=True)
    return code == 0

def ensure_command(cmd: str, install_hint: str) -> None:
    """اطمینان از وجود دستور، در غیر این صورت راهنمایی"""
    if not command_exists(cmd):
        console.error(f"دستور '{cmd}' در سیستم یافت نشد.")
        console.info(f"💡 راه‌حل: {install_hint}")
        raise RuntimeError(f"دستور ضروری یافت نشد: {cmd}")