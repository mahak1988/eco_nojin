#!/usr/bin/env python3
"""Quick commit with PATH setup"""
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# افزودن git به PATH
for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
    if Path(p).exists() and p not in os.environ["PATH"]:
        os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

os.chdir(PROJECT_ROOT)

subprocess.run("git add .", shell=True, check=True)
subprocess.run(
    'git commit -m "fix(crypto): correct test import typo (mock_generator → mockGenerator)"',
    shell=True, check=True
)
subprocess.run("git push origin main", shell=True, check=True)
print("✓ commit و push موفق")