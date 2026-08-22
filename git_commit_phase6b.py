"""Phase 6b Git Commit — Final Scientific Refinement"""
import subprocess
from pathlib import Path

GIT = r"C:\Program Files\Git\cmd\git.exe"
ROOT = Path(r"D:\eco_nojin")

def run(cmd, desc):
    print(f"\n🔧 {desc}")
    r = subprocess.run([GIT] + cmd, cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    print(f"   {'✅' if r.returncode==0 else '❌'}")
    if r.stdout and len(r.stdout) < 500:
        print(f"   {r.stdout.strip()[:400]}")
    return r.returncode == 0

run(["add", "sandbox/phase6b_final_refinement.py"], "Staging Phase 6b")
run(["status", "--short"], "Status")

msg = """refactor(science): Phase 6b - Final Köppen refinement + crisis-aware PRSP

Scientific improvements to Global Watchdog:
1. KGCv3: Correct arid detection with proper B-before-A/C/D precedence
2. PRSPv3: Crisis-aware recommendations — WBI>80 forces arid-crisis context
   (ensures Yemen, Somalia get desalination/MAR not generic wetland)
3. Time-to-bankruptcy: realistic with governance adaptation factor
4. Uncertainty bounds: ±15% on all composite indices
5. WERI: sigmoid soft-cap to avoid over-aggressive 100% readings

Validated: Somalia=Aw ✓, Iran=Csa ✓, California=Csa ✓
Known limitation: Sudan, Yemen, Netherlands Köppen sensitive to preset
data quality — will be resolved in Phase 7 with WorldClim real data.

Crisis intervention context now produces appropriate recommendations:
- Yemen (WBI=90): drip irrigation + solar desalination + emergency trucking
- Somalia (WBI=86): same crisis protocol
- Netherlands (WBI=3): flood preparedness + biodiversity conservation"""

run(["commit", "-m", msg], "Committing")
run(["push", "origin", "main"], "Pushing")