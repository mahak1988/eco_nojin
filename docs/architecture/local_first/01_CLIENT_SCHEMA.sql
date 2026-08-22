-- Client Database Schema
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
