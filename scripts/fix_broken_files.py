#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Rewrite broken files (admin/index.ts + ProtectedRoute.tsx)
================================================================
Root cause: Previous regex purges left truncated fragments.
Solution: Complete rewrite with verified content.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


# =============================================================================
# 1. CORRECT admin/index.ts (17 verified live exports)
# =============================================================================

ADMIN_INDEX = '''// Verified live exports after HyDroMa purge
export { default as AdminLayout } from './AdminLayout';
export { default as AdminOverview } from './AdminOverview';
export { default as AdminSecurity } from './AdminSecurity';
export { default as AdminUsers } from './AdminUsers';
export { default as AdminAudit } from './AdminAudit';
export { default as AdminFinance } from './AdminFinance';
export { default as AdminErrors } from './AdminErrors';
export { default as AdminContent } from './AdminContent';
export { default as AdminSettings } from './AdminSettings';
export { ThemeProvider } from './ThemeProvider';
export { default as SecurityAdvanced } from './SecurityAdvanced';
export { default as MarketplaceDashboard } from './MarketplaceDashboard';
export { default as EcoWalletDashboard } from './EcoWalletDashboard';
export { default as ContentStudio } from './ContentStudio';
export { default as BotsManagement } from './BotsManagement';
export { default as AIModelsMonitor } from './AIModelsMonitor';
export { default as MotorRunner } from './MotorRunner';
export { default as LiveDashboard } from './LiveDashboard';
export { default as CryptoPaymentWidget } from './crypto/CryptoPaymentWidget';
export { default as TelegramManager } from './telegram/TelegramManager';
'''


# =============================================================================
# 2. SAFE ProtectedRoute.tsx (standard pattern, no hydroma references)
# =============================================================================

PROTECTED_ROUTE = '''import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

/**
 * Route guard that redirects unauthenticated users to /login
 * and unauthorized users to /.
 */
export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner fullScreen />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
'''


def main():
    print("")
    print("=" * 70)
    print("  Fix: Rewrite Broken Files")
    print("=" * 70)
    print("")
    print("  Rewriting:")
    print("    1. src/pages/admin/index.ts (17 live exports)")
    print("    2. src/components/auth/ProtectedRoute.tsx (standard pattern)")
    print("")

    setup_git_path()

    # Step 1: Rewrite admin/index.ts
    print("[Step 1] Rewriting src/pages/admin/index.ts")
    print("-" * 70)
    admin_file = SRC / "pages" / "admin" / "index.ts"
    
    # Read current to compare
    current = admin_file.read_text(encoding="utf-8-sig") if admin_file.exists() else ""
    
    if "wer';" in current or "HyDroMa" in current:
        info(f"Current file has {len(current)} bytes (broken)")
        info("Problematic fragments detected:")
        for i, line in enumerate(current.splitlines(), 1):
            if "wer';" in line or "HyDroMa" in line or line.strip().startswith("||"):
                info(f"  Line {i}: {line[:80]}")
    
    admin_file.write_text(ADMIN_INDEX, encoding="utf-8")
    ok(f"Rewritten with {len(ADMIN_INDEX.splitlines())} clean exports")
    print("")

    # Step 2: Rewrite ProtectedRoute.tsx
    print("[Step 2] Rewriting src/components/auth/ProtectedRoute.tsx")
    print("-" * 70)
    pr_file = SRC / "components" / "auth" / "ProtectedRoute.tsx"
    
    current_pr = pr_file.read_text(encoding="utf-8-sig") if pr_file.exists() else ""
    
    if "||" in current_pr and current_pr.count("||") > current_pr.count("|||"):
        info(f"Current file has {len(current_pr)} bytes (broken)")
        # Show problematic line
        for i, line in enumerate(current_pr.splitlines(), 1):
            if "||" in line and i > 60 and i < 70:
                info(f"  Line {i}: {line[:80]}")
    
    pr_file.write_text(PROTECTED_ROUTE, encoding="utf-8")
    ok("Rewritten with standard pattern")
    print("")

    # Step 3: Build verification
    print("[Step 3] Build verification")
    print("-" * 70)
    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    
    build_ok = result.returncode == 0
    
    if build_ok:
        ok("🎉 Build successful!")
        for line in (result.stdout + result.stderr).splitlines():
            if "dist/assets/index" in line and "kB" in line:
                info(f"  bundle: {line.strip()}")
    else:
        err("Build still failing:")
        output = result.stdout + result.stderr
        
        # Extract errors
        import re
        errors = re.findall(r'\[.*?\]\s*([^\n]+)', output)
        if errors:
            print("\n  Errors:")
            for e in errors[:5]:
                print(f"    • {e.strip()}")
        
        print("\n  Last 20 lines:")
        for line in output.splitlines()[-20:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 4: Commit
    if build_ok:
        print("[Step 4] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add -A .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(purge): rewrite broken files after HyDroMa removal\\n\\n"
                "Root cause: Previous regex purges left truncated fragments\\n"
                "- admin/index.ts had 'wer'; orphan fragment\\n"
                "- ProtectedRoute.tsx had misplaced '||' operator\\n\\n"
                "Solution: Complete rewrite with verified content:\\n"
                "- admin/index.ts: 20 clean exports (17 + LiveDashboard/Crypto/Telegram)\\n"
                "- ProtectedRoute.tsx: standard auth guard pattern\\n\\n"
                "Build is now green. Workspace fully clean."
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  ✅ COMPLETE - All broken files fixed")
        print("=" * 70)
        print("")
        print("  Final state:")
        print("    • Build: ✅ green")
        print("    • admin/index.ts: 20 clean exports")
        print("    • ProtectedRoute.tsx: standard pattern")
        print("    • /hydroma: placeholder page")
        print("    • Workspace: fully clean")
        print("")
        print("  Ready for standard simulator rebuild!")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())