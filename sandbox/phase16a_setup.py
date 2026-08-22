"""
Phase 16a: Create Local-First Architecture Docs
================================================
فقط ساختار پوشه‌ها و اسناد SQL/Markdown را ایجاد می‌کند.
"""
from pathlib import Path

ROOT = Path(r"D:\eco_nojin\docs\architecture\local_first")
ROOT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 1. README
# ============================================================================

readme = """# Local-First Hybrid Architecture

## Overview

معماری Local-First Hybrid برای پلتفرم EcoNojin:
- همه داده‌های کاربر روی دستگاه خودش ذخیره می‌شود
- سرور فقط auth + encrypted sync blobs
- هزینه سرور ~$20-50/ماه (به جای $1500-7000)
- حریم خصوصی zero-knowledge
- کارکرد آفلاین

## Files

| # | File | Description |
|---|------|-------------|
| 01 | `CLIENT_SCHEMA.sql` | Schema دیتابیس دستگاه کاربر |
| 02 | `SERVER_SCHEMA.sql` | Schema دیتابیس سرور (minimal) |
| 03 | `PWA_MANIFEST.json` | PWA manifest |
| 04 | `SERVICE_WORKER.js` | Offline capability |
| 05 | `INDEXEDDB_CLIENT.js` | Client storage |
| 06 | `SYNC_PROTOCOL.md` | Encrypted sync |
| 07 | `SERVER_ENDPOINT.py` | Minimal FastAPI |
| 08 | `COST_ANALYSIS.md` | Economic analysis |

## References

- Linear's local-first: https://linear.app/blog/local-first
- Signal protocol: https://signal.org/docs/
- CRDTs: https://crdt.tech/
- NIST PBKDF2: NIST SP 800-132

## Stack

- **Client**: IndexedDB + WebAssembly + Service Workers
- **Sync**: AES-256-GCM encrypted deltas + CRDTs
- **Server**: Supabase Free Tier + Cloudflare Workers
- **No Docker Required**: 100% cloud-native managed services
"""

(ROOT / "README.md").write_text(readme, encoding="utf-8")
print("Created: README.md")


# ============================================================================
# 2. Client Schema (SQLite / IndexedDB)
# ============================================================================

client_schema = """-- Client Database Schema
-- همه داده‌های کاربر روی دستگاه خودش ذخیره می‌شود
-- Runs in: IndexedDB (browser) / SQLite (desktop) / Realm (mobile)

CREATE TABLE IF NOT EXISTS local_user (
    id TEXT PRIMARY KEY,
    email_hash TEXT NOT NULL,
    display_name TEXT,
    subscription_tier TEXT,
    created_at TEXT NOT NULL,
    last_sync_at TEXT
);

CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    region_name TEXT NOT NULL,
    crop_type TEXT NOT NULL,
    lat REAL,
    lon REAL,
    
    koppen TEXT,
    wbi TEXT,
    ewsi TEXT,
    hyrue TEXT,
    ecsi TEXT,
    hdvi TEXT,
    epia TEXT,
    hpheno TEXT,
    esri TEXT,
    hlhs TEXT,
    
    execution_time_ms REAL,
    model_version TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_to_server INTEGER DEFAULT 0,
    
    lamport_clock INTEGER DEFAULT 0,
    
    UNIQUE(user_id, region_name, crop_type)
);

CREATE TABLE IF NOT EXISTS satellite_cache (
    id TEXT PRIMARY KEY,
    tile_id TEXT NOT NULL,
    acquisition_date TEXT NOT NULL,
    cloud_cover REAL,
    scene_id TEXT,
    local_file_path TEXT,
    downloaded_at TEXT NOT NULL,
    expires_at TEXT,
    
    UNIQUE(tile_id, acquisition_date)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    id TEXT PRIMARY KEY,
    region_name TEXT NOT NULL,
    label TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    encrypted_payload TEXT,
    created_at TEXT NOT NULL,
    sent_at TEXT,
    retry_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_sync ON analyses(synced_to_server);
CREATE INDEX IF NOT EXISTS idx_sync_queue_pending ON sync_queue(sent_at) WHERE sent_at IS NULL;
"""

(ROOT / "01_CLIENT_SCHEMA.sql").write_text(client_schema, encoding="utf-8")
print("Created: 01_CLIENT_SCHEMA.sql")


# ============================================================================
# 3. Server Schema (Minimal — PostgreSQL)
# ============================================================================

server_schema = """-- Server Database Schema (MINIMAL)
-- فقط آنچه قانوناً لازم است ذخیره می‌شود
-- Target: Supabase Free Tier / Neon.tech Free Tier (NO DOCKER)

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email_hash TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    subscription_tier TEXT DEFAULT 'free',
    api_key TEXT UNIQUE NOT NULL,
    email_verified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    key_hash TEXT UNIQUE NOT NULL,
    name TEXT,
    permissions TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    revoked INTEGER DEFAULT 0
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    token_hash TEXT UNIQUE NOT NULL,
    device_info TEXT,
    ip_hash TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked INTEGER DEFAULT 0
);

-- فقط encrypted blobs (server نمی‌تواند محتویات را ببیند)
CREATE TABLE encrypted_sync_blobs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    blob_key_hash TEXT NOT NULL,
    encrypted_data BYTEA NOT NULL,
    iv BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    UNIQUE(user_id, blob_key_hash)
);

-- Anonymous telemetry (بدون هویت)
CREATE TABLE anonymous_telemetry (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_data JSONB,
    country_code TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email_hash ON users(email_hash);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_sync_blobs_user ON encrypted_sync_blobs(user_id);
CREATE INDEX idx_sync_blobs_expires ON encrypted_sync_blobs(expires_at);
"""

(ROOT / "02_SERVER_SCHEMA.sql").write_text(server_schema, encoding="utf-8")
print("Created: 02_SERVER_SCHEMA.sql")


# ============================================================================
# 4. Sync Protocol
# ============================================================================

sync_protocol = """# Sync Protocol: Zero-Knowledge Encrypted Deltas

## Overview

Client و سرور فقط deltas (تغییرات) را به صورت end-to-end encrypted 
مبادله می‌کنند. سرور نمی‌تواند محتویات را بخواند.

## Flow: Client to Server (Sync Up)

Client:
  1. Collect unsynced changes from sync_queue
  2. Encrypt each change with user's master key (AES-256-GCM)
  3. POST /api/v1/sync/push
     Body: {
       "changes": [
         {
           "id": "...",
           "table": "analyses",
           "operation": "insert",
           "encrypted_payload": "...",
           "iv": "...",
           "lamport_clock": 42
         }
       ]
     }

Server:
  1. Validate auth
  2. Store encrypted blobs (opaque storage)
  3. Update vector clock
  4. Return: { "accepted": [...], "conflicts": [...] }

## Flow: Server to Client (Sync Down)

Client:
  1. GET /api/v1/sync/pull?since=<last_sync_timestamp>

Server:
  1. Return all encrypted blobs updated since timestamp
  2. Include vector clock for conflict resolution

Client:
  1. Decrypt each blob with master key
  2. Apply to local DB
  3. Resolve conflicts using Lamport clocks
  4. Update last_sync_at

## Conflict Resolution: Lamport Clocks

Example:
  A: lamport=5, value=X
  B: lamport=7, value=Y
  Result: B wins (higher clock = newer)

If equal: use deterministic tiebreaker (record_id hash)

## Bandwidth Efficiency

| Operation | Data Sent |
|-----------|-----------|
| New analysis | ~5 KB (encrypted) |
| Update | ~1 KB (delta only) |
| Delete | ~100 bytes |

For 1000 users x 10 analyses/day = 50 MB/day total (negligible)
"""

(ROOT / "06_SYNC_PROTOCOL.md").write_text(sync_protocol, encoding="utf-8")
print("Created: 06_SYNC_PROTOCOL.md")


# ============================================================================
# 5. Cost Analysis
# ============================================================================

cost_analysis = """# Cost Analysis: Traditional SaaS vs Local-First

## Traditional SaaS Architecture (Current)

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| PostgreSQL RDS | $200-500 | All user data |
| S3 Storage | $100-300 | Analysis results, imagery |
| EC2/EKS Compute | $500-2000 | API servers, workers |
| CDN | $50-200 | Content delivery |
| Load Balancer | $50-100 | |
| Monitoring | $50-100 | |
| **Total** | **$950-3200/month** | |

## Local-First Hybrid (Proposed) — NO DOCKER

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| Supabase Free Tier | $0 | Auth + PostgreSQL |
| Cloudflare Workers | $0-5 | Free tier (100K req/day) |
| Cloudflare R2 | $5-15 | Encrypted blobs only |
| Vercel Free Tier | $0 | Frontend hosting |
| **Total** | **$5-20/month** | |

## Scaling to 1M Users

| Metric | Traditional | Local-First |
|--------|-------------|-------------|
| Storage cost | $50,000/mo | $500/mo |
| Compute cost | $30,000/mo | $2,000/mo |
| **Total** | **$80,000/mo** | **$2,500/mo** |
| **Savings** | — | **97%** |

## Privacy Benefits

- GDPR compliant by design
- Zero-knowledge server
- No vendor lock-in
- Works offline

## User Experience

- Instant response (local storage)
- Offline capability
- Installable PWA
- Cross-device sync

## Company References

| Company | Model | Users |
|---------|-------|-------|
| Linear | Local-first issue tracking | 100K+ teams |
| Figma | Local compute + cloud sync | 4M+ users |
| Obsidian | 100% local notes | 2M+ users |
| Signal | Local messages + encrypted sync | 40M+ users |
| Notion | Local cache + sync | 30M+ users |
"""

(ROOT / "08_COST_ANALYSIS.md").write_text(cost_analysis, encoding="utf-8")
print("Created: 08_COST_ANALYSIS.md")


# ============================================================================
# Summary
# ============================================================================

print()
print("=" * 70)
print("Phase 16a: Documentation files created")
print("=" * 70)
print(f"Location: {ROOT}")
print()
print("Files created:")
for f in sorted(ROOT.iterdir()):
    size_kb = f.stat().st_size / 1024
    print(f"  - {f.name} ({size_kb:.1f} KB)")
print()
print("Next: python sandbox\\phase16b_code.py")