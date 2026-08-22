"""Quick Git fix using full path"""
import subprocess
from pathlib import Path

GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = Path(r"D:\eco_nojin")

def run(cmd, desc):
    print(f"\n🔧 {desc}")
    r = subprocess.run([GIT] + cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"   {'✅' if r.returncode==0 else '❌'} {r.stdout[:300] if r.stdout else r.stderr[:300]}")
    return r.returncode == 0

run(["add", "."], "Staging")
run(["status", "--short"], "Status")

msg = """feat(science): Phase 4a - Professional Hydroma models library

8 proprietary scientific models with enterprise-grade architecture:
EWSI, HY-RUE, ECSI, HDVI, EPIA, H-Pheno, ESRI, HLHS.
Includes validation data, uncertainty quantification, sensitivity analysis."""

run(["commit", "-m", msg], "Committing")
run(["push", "origin", "main"], "Pushing")