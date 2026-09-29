#!/bin/bash
# scripts/backup.sh - Create timestamped backup of critical data
# Backs up: database, .env (secrets redacted), config

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$PROJECT_ROOT/backups/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo "Creating backup at: $BACKUP_DIR"

DB_PATH="$PROJECT_ROOT/data/econojin.db"
if [ -f "$DB_PATH" ]; then
    python - "$DB_PATH" "$BACKUP_DIR/econojin.db" <<'PY'
import sqlite3
import sys

source = sqlite3.connect(sys.argv[1])
target = sqlite3.connect(sys.argv[2])
try:
    source.backup(target)
finally:
    target.close()
    source.close()
PY
    echo "  [OK] Database backed up"
else
    echo "  [SKIP] Database not found at $DB_PATH"
fi

# 2. Backup .env with secrets redacted
ENV_PATH="$PROJECT_ROOT/.env"
if [ -f "$ENV_PATH" ]; then
    sed -E 's/([^=]+=)(.*)/***REDACTED***/g' "$ENV_PATH" > "$BACKUP_DIR/.env.redacted"
    echo "  [OK] .env backed up (secrets redacted)"
else
    echo "  [SKIP] .env not found"
fi

# 3. Backup config files
for cfg in pyproject.toml requirements.txt alembic.ini deploy/docker-compose.yml; do
    if [ -f "$PROJECT_ROOT/$cfg" ]; then
        mkdir -p "$BACKUP_DIR/$(dirname "$cfg")"
        cp "$PROJECT_ROOT/$cfg" "$BACKUP_DIR/$cfg"
    fi
done
echo "  [OK] Config files backed up"

# 4. Create manifest
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
Eco Nojin Backup Manifest
=========================
Timestamp: $TIMESTAMP
Date: $(date)
Host: $(hostname)

Contents:
- data/econojin.db       (SQLite database)
- .env.redacted          (environment with secrets redacted)
- pyproject.toml         (project config)
- requirements.txt       (dependencies)
- alembic.ini            (migration config)
- deploy/docker-compose.yml (optional Podman infrastructure)
EOF

echo "  [OK] Manifest created"

# 5. Clean up old backups (keep last 30 days)
find "$PROJECT_ROOT/backups" -type d -name "20*" -mtime +30 -exec rm -rf {} + 2>/dev/null || true

echo "Backup complete: $BACKUP_DIR"