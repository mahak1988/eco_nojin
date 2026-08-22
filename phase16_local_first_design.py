"""
Phase 16: Local-First Architecture Design + POC
===============================================

معماری: Local-First Hybrid (Linear/Obsidian/Signal style)

هدف:
- همه داده‌های کاربر روی دستگاه خودش (mobile/desktop/browser)
- سرور فقط: auth + API keys + encrypted sync blobs
- هزینه سرور: ~$20-50/ماه (به جای $1500-7000)
- حریم خصوصی: Zero-knowledge server
- GDPR/CCPA compliant by design

تکنولوژی‌ها:
- Client: IndexedDB (web) / SQLite (desktop) / Secure Enclave (mobile)
- Compute: WebAssembly (C++ models in browser)
- Sync: End-to-end encrypted deltas
- Server: PostgreSQL (auth) + S3/R2 (encrypted blobs)
"""
from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# 1. Client-Side Storage Schema (IndexedDB / Local SQLite)
# ============================================================================

CLIENT_SCHEMA = '''
-- Client Database Schema (runs in browser IndexedDB or local SQLite)
-- همه داده‌های کاربر روی دستگاه خودش ذخیره می‌شود

CREATE TABLE IF NOT EXISTS local_user (
    id TEXT PRIMARY KEY,           -- UUID from server
    email_hash TEXT NOT NULL,      -- فقط hash (email واقعی روی سرور)
    display_name TEXT,
    subscription_tier TEXT,        -- free / pro / enterprise
    created_at TEXT NOT NULL,
    last_sync_at TEXT
);

CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,           -- UUID v4
    user_id TEXT NOT NULL,
    region_name TEXT NOT NULL,
    crop_type TEXT NOT NULL,
    lat REAL,
    lon REAL,
    
    -- Results (stored locally, NEVER sent to server in plaintext)
    koppen TEXT,    -- JSON
    wbi TEXT,       -- JSON
    ewsi TEXT,      -- JSON
    hyrue TEXT,     -- JSON
    ecsi TEXT,      -- JSON
    hdvi TEXT,      -- JSON
    epia TEXT,      -- JSON
    hpheno TEXT,    -- JSON
    esri TEXT,      -- JSON
    hlhs TEXT,      -- JSON
    
    execution_time_ms REAL,
    model_version TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_to_server INTEGER DEFAULT 0,  -- 0 = local only, 1 = synced (encrypted)
    
    -- Sync metadata (CRDT)
    lamport_clock INTEGER DEFAULT 0,
    vector_clock TEXT,
    
    UNIQUE(user_id, region_name, crop_type)
);

CREATE TABLE IF NOT EXISTS satellite_cache (
    id TEXT PRIMARY KEY,
    tile_id TEXT NOT NULL,
    acquisition_date TEXT NOT NULL,
    cloud_cover REAL,
    scene_id TEXT,
    local_file_path TEXT,    -- path to local COG file
    downloaded_at TEXT NOT NULL,
    expires_at TEXT,
    
    UNIQUE(tile_id, acquisition_date)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT,                   -- JSON
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
    operation TEXT NOT NULL,       -- insert / update / delete
    encrypted_payload TEXT,        -- AES-256 encrypted, server cannot read
    created_at TEXT NOT NULL,
    sent_at TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_sync ON analyses(synced_to_server);
CREATE INDEX IF NOT EXISTS idx_sync_queue_pending ON sync_queue(sent_at) WHERE sent_at IS NULL;
'''


# ============================================================================
# 2. Server-Side Minimal Schema (Only essential data)
# ============================================================================

SERVER_SCHEMA = '''
-- Server Database Schema (MINIMAL — برای صرفه‌جویی در هزینه)
-- فقط آنچه قانوناً لازم است ذخیره می‌شود

CREATE TABLE users (
    id TEXT PRIMARY KEY,                      -- UUID v4
    email_hash TEXT UNIQUE NOT NULL,          -- bcrypt hash of email
    password_hash TEXT NOT NULL,              -- bcrypt hash
    display_name TEXT,
    subscription_tier TEXT DEFAULT 'free',    -- free/pro/enterprise
    api_key TEXT UNIQUE NOT NULL,             -- for rate limiting
    email_verified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    -- Rate limiting
    daily_request_count INTEGER DEFAULT 0,
    rate_limit_reset_at TIMESTAMP
);

CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    key_hash TEXT UNIQUE NOT NULL,
    name TEXT,
    permissions TEXT,                -- JSON array
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    revoked INTEGER DEFAULT 0
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    token_hash TEXT UNIQUE NOT NULL,
    device_info TEXT,                -- user agent, platform
    ip_hash TEXT,                    -- hash of IP (for security)
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked INTEGER DEFAULT 0
);

-- فقط encrypted blobs (server نمی‌تواند محتویات را ببیند)
-- برای sync بین دستگاه‌های کاربر
CREATE TABLE encrypted_sync_blobs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    blob_key_hash TEXT NOT NULL,     -- hash of key, not key itself
    encrypted_data BYTEA NOT NULL,   -- AES-256-GCM, server cannot decrypt
    iv BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,            -- TTL
    
    UNIQUE(user_id, blob_key_hash)
);

-- Anonymous telemetry (برای بهبود محصول، بدون هویت)
CREATE TABLE anonymous_telemetry (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,        -- 'analysis', 'login', 'error'
    event_data JSONB,                -- anonymized
    country_code TEXT,               -- from IP, for regional analytics
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email_hash ON users(email_hash);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sync_blobs_user ON encrypted_sync_blobs(user_id);
CREATE INDEX idx_sync_blobs_expires ON encrypted_sync_blobs(expires_at);
CREATE INDEX idx_telemetry_created ON anonymous_telemetry(created_at);
'''


# ============================================================================
# 3. Client-Side Encryption (Zero-Knowledge)
# ============================================================================

@dataclass
class EncryptedPayload:
    """Encrypted payload for sync to server (server cannot decrypt)."""
    ciphertext: str           # base64
    iv: str                   # base64, 16 bytes
    salt: str                 # base64, 32 bytes
    key_id: str               # reference to user's key (stored locally)
    version: int = 1
    algorithm: str = "AES-256-GCM"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ClientEncryption:
    """
    Zero-Knowledge Encryption for Local-First Architecture.
    
    - Key derivation: PBKDF2 با 600,000 iterations
    - Encryption: AES-256-GCM
    - کلید رمزگذاری فقط روی دستگاه کاربر است
    - سرور هیچ‌گاه کلید را نمی‌بیند
    
    Reference: NIST SP 800-132 (PBKDF2), NIST SP 800-38D (GCM)
    """
    
    def __init__(self, user_password: str, salt: Optional[bytes] = None):
        # در production واقعی: از Web Crypto API یا libsodium استفاده می‌شود
        # اینجا فقط schema را نشان می‌دهیم
        import hashlib
        import hmac
        
        self.salt = salt or secrets.token_bytes(32)
        
        # PBKDF2-HMAC-SHA256 — 600,000 iterations (OWASP 2023 recommendation)
        self.master_key = hashlib.pbkdf2_hmac(
            'sha256',
            user_password.encode('utf-8'),
            self.salt,
            iterations=600000,
            dklen=32,
        )
    
    def encrypt(self, plaintext: Dict[str, Any]) -> EncryptedPayload:
        """
        Encrypt data before sending to server.
        Server stores ciphertext but CANNOT decrypt.
        """
        import base64
        
        data_bytes = json.dumps(plaintext, ensure_ascii=False).encode('utf-8')
        iv = secrets.token_bytes(12)  # GCM standard
        
        # در production: از cryptography.fernet یا libsodium استفاده می‌شود
        # اینجا شبیه‌سازی می‌کنیم
        import hashlib
        key_stream = hashlib.sha256(self.master_key + iv).digest()
        ciphertext = bytes(a ^ b for a, b in zip(data_bytes, key_stream * ((len(data_bytes) // 32) + 1)))
        
        return EncryptedPayload(
            ciphertext=base64.b64encode(ciphertext).decode('ascii'),
            iv=base64.b64encode(iv).decode('ascii'),
            salt=base64.b64encode(self.salt).decode('ascii'),
            key_id=hashlib.sha256(self.master_key).hexdigest()[:16],
        )
    
    def decrypt(self, payload: EncryptedPayload) -> Dict[str, Any]:
        """Decrypt data received from server."""
        import base64
        import hashlib
        
        ciphertext = base64.b64decode(payload.ciphertext)
        iv = base64.b64decode(payload.iv)
        
        key_stream = hashlib.sha256(self.master_key + iv).digest()
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, key_stream * ((len(ciphertext) // 32) + 1)))
        
        return json.loads(plaintext.decode('utf-8'))


# ============================================================================
# 4. Local-First Client (Browser PWA)
# ============================================================================

PWA_MANIFEST = '''
{
  "name": "Hydroma Global Watchdog",
  "short_name": "Hydroma",
  "description": "Local-first water security analysis platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0e27",
  "theme_color": "#1e40af",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "categories": ["productivity", "utilities"],
  "shortcuts": [
    {
      "name": "New Analysis",
      "url": "/analyze",
      "description": "Run a new regional analysis"
    },
    {
      "name": "My Analyses",
      "url": "/history",
      "description": "View saved analyses"
    }
  ]
}
'''


SERVICE_WORKER_JS = '''// service-worker.js
// Enables offline-first capability

const CACHE_NAME = 'hydroma-v1';
const OFFLINE_URL = '/offline.html';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/app.js',
  '/wasm/hydroma_models.wasm',  // C++ models compiled to WASM
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  OFFLINE_URL,
];

// Install: precache critical assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: network-first with cache fallback
self.addEventListener('fetch', (event) => {
  // Skip non-GET
  if (event.request.method !== 'GET') return;
  
  // Skip API calls (go direct to server or IndexedDB)
  if (event.request.url.includes('/api/')) return;
  
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone and cache successful response
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request).then(r => r || caches.match(OFFLINE_URL)))
  );
});

// Background sync: retry failed encrypted syncs
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-analyses') {
    event.waitUntil(syncPendingAnalyses());
  }
});

async function syncPendingAnalyses() {
  // Read from sync_queue in IndexedDB, send encrypted to server
  // See sync.js for implementation
  console.log('Background sync: sending pending encrypted analyses');
}
'''


INDEXEDDB_CLIENT_JS = '''// client-storage.js
// IndexedDB wrapper for local-first storage

class LocalStorage {
  constructor() {
    this.dbName = 'hydroma_db';
    this.version = 1;
    this.db = null;
  }
  
  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // analyses table
        if (!db.objectStoreNames.contains('analyses')) {
          const store = db.createObjectStore('analyses', { keyPath: 'id' });
          store.createIndex('user_id', 'user_id');
          store.createIndex('region_name', 'region_name');
          store.createIndex('created_at', 'created_at');
          store.createIndex('synced', 'synced_to_server');
        }
        
        // satellite cache
        if (!db.objectStoreNames.contains('satellite_cache')) {
          const store = db.createObjectStore('satellite_cache', { keyPath: 'id' });
          store.createIndex('tile_id', 'tile_id');
          store.createIndex('acquisition_date', 'acquisition_date');
        }
        
        // user preferences
        if (!db.objectStoreNames.contains('preferences')) {
          db.createObjectStore('preferences', { keyPath: 'key' });
        }
        
        // sync queue
        if (!db.objectStoreNames.contains('sync_queue')) {
          const store = db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
          store.createIndex('sent_at', 'sent_at');
        }
      };
    });
  }
  
  async saveAnalysis(analysis) {
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction('analyses', 'readwrite');
      const store = tx.objectStore('analyses');
      const request = store.put(analysis);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  
  async getAnalysis(id) {
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction('analyses', 'readonly');
      const store = tx.objectStore('analyses');
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  
  async getAllAnalyses(userId) {
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction('analyses', 'readonly');
      const store = tx.objectStore('analyses');
      const index = store.index('user_id');
      const request = index.getAll(userId);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  
  async queueSync(table, recordId, operation, encryptedPayload) {
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction('sync_queue', 'readwrite');
      const store = tx.objectStore('sync_queue');
      const request = store.add({
        table_name: table,
        record_id: recordId,
        operation: operation,
        encrypted_payload: encryptedPayload,
        created_at: new Date().toISOString(),
        retry_count: 0,
      });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
}

// Usage example
async function runAnalysisAndSave(regionName, cropType) {
  const storage = new LocalStorage();
  await storage.init();
  
  // Call local WASM model (no server needed!)
  const analysis = await window.hydromaModels.analyze(regionName, cropType);
  
  // Save locally (instant, offline works)
  await storage.saveAnalysis({
    id: crypto.randomUUID(),
    user_id: getCurrentUserId(),
    region_name: regionName,
    crop_type: cropType,
    ...analysis,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    synced_to_server: 0,
  });
  
  // Queue encrypted sync for background
  const encrypted = await encryptForServer(analysis);
  await storage.queueSync('analyses', analysis.id, 'insert', encrypted.to_json());
  
  // Trigger background sync
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    const reg = await navigator.serviceWorker.ready;
    await reg.sync.register('sync-analyses');
  }
}
'''


# ============================================================================
# 5. Sync Protocol (Encrypted Deltas)
# ============================================================================

SYNC_PROTOCOL_DOC = '''
# Sync Protocol: Zero-Knowledge Encrypted Deltas

## Overview

Client و سرور فقط **deltas** (تغییرات) را به صورت **end-to-end encrypted** 
مبادله می‌کنند. سرور نمی‌تواند محتویات را بخواند.

## Flow

### 1. Client → Server (Sync Up)
