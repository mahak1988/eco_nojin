#!/bin/bash
# scripts/maintenance.sh - Daily maintenance routine (< 15 min)
# Runs: dependency audit, secret scan, tests with coverage, migration check, backup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/backups/maintenance_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$PROJECT_ROOT/backups"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== Starting daily maintenance ==="

# 1. Dependency audit
log "Step 1/5: Running pip-audit..."
if command -v pip-audit &>/dev/null; then
    pip-audit --upgrade || log "WARNING: pip-audit found issues"
else
    log "WARNING: pip-audit not installed, skipping"
fi

# 2. Secret scan
log "Step 2/5: Running gitleaks..."
if command -v gitleaks &>/dev/null; then
    gitleaks detect --source "$PROJECT_ROOT" --no-git -v || log "WARNING: gitleaks found issues"
else
    log "WARNING: gitleaks not installed, skipping"
fi

# 3. Run tests with coverage
log "Step 3/5: Running tests with coverage..."
cd "$PROJECT_ROOT/services"
python -m pytest -q --tb=short --cov=engine --cov=services --cov-report=term || log "WARNING: tests had failures"

# 4. Check migration chain
log "Step 4/5: Checking migration chain..."
cd "$PROJECT_ROOT"
if command -v alembic &>/dev/null; then
    alembic current || log "WARNING: alembic check failed"
else
    log "WARNING: alembic not available, skipping"
fi

# 5. Backup
log "Step 5/5: Running backup..."
if [ -f "$PROJECT_ROOT/scripts/backup.sh" ]; then
    bash "$PROJECT_ROOT/scripts/backup.sh" || log "WARNING: backup failed"
else
    log "WARNING: backup.sh not found, skipping"
fi

log "=== Daily maintenance complete ==="
log "Log saved to: $LOG_FILE"