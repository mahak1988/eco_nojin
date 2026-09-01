#!/usr/bin/env python3
"""Commit Camera Fix with PATH"""
import structlog

logger = structlog.get_logger()
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# افزودن git به PATH
git_paths = [
    r"C:\Program Files\Git\cmd",
    r"C:\Program Files\Git\bin",
]
for p in git_paths:
    if Path(p).exists() and p not in os.environ["PATH"]:
        os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

os.chdir(PROJECT_ROOT)

subprocess.run("git add .", shell=True, check=True)
subprocess.run(
    'git commit -m "fix(hydroma): correct default camera view for proper terrain visibility"',
    shell=True, check=True
)
subprocess.run("git push origin main", shell=True, check=True)
logger.info("✓ commit و push موفق بود")
