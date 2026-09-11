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

# 1. Backup database
DB_PATH="$PROJECT_ROOT/hydroma_research.db"
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/hydroma_research.db"
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
for cfg in pyproject.toml requirements.txt docker-compose.yml; do
    if [ -f "$PROJECT_ROOT/$cfg" ]; then
        cp "$PROJECT_ROOT/$cfg" "$BACKUP_DIR/"
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
- hydroma_research.db    (database, may be empty if not found)
- .env.redacted          (environment with secrets redacted)
- pyproject.toml         (project config)
- requirements.txt       (dependencies)
- docker-compose.yml     (container config, if exists)
EOF

echo "  [OK] Manifest created"

# 5. Clean up old backups (keep last 30 days)
find "$PROJECT_ROOT/backups" -type d -name "20*" -mtime +30 -exec rm -rf {} + 2>/dev/null || true

echo "Backup complete: $BACKUP_DIR"