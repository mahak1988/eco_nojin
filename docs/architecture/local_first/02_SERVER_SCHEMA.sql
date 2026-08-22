-- Server Database Schema (MINIMAL)
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
