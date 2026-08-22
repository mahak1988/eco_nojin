"""
Phase 16b: Create Local-First Code Files
=========================================
کدهای JavaScript (client) و Python (server) را ایجاد می‌کند.
"""
from pathlib import Path

ROOT = Path(r"D:\eco_nojin\docs\architecture\local_first")
ROOT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 1. PWA Manifest
# ============================================================================

pwa_manifest = """{
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
"""

(ROOT / "03_PWA_MANIFEST.json").write_text(pwa_manifest, encoding="utf-8")
print("Created: 03_PWA_MANIFEST.json")


# ============================================================================
# 2. Service Worker
# ============================================================================

service_worker = """// service-worker.js
// Enables offline-first capability

const CACHE_NAME = 'hydroma-v1';
const OFFLINE_URL = '/offline.html';

const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/app.js',
  '/wasm/hydroma_models.wasm',
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
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/')) return;
  
  event.respondWith(
    fetch(event.request)
      .then((response) => {
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
  console.log('Background sync: sending pending encrypted analyses');
  // Read from sync_queue in IndexedDB, send encrypted to server
}
"""

(ROOT / "04_SERVICE_WORKER.js").write_text(service_worker, encoding="utf-8")
print("Created: 04_SERVICE_WORKER.js")


# ============================================================================
# 3. IndexedDB Client
# ============================================================================

indexeddb_client = """// client-storage.js
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
        
        if (!db.objectStoreNames.contains('analyses')) {
          const store = db.createObjectStore('analyses', { keyPath: 'id' });
          store.createIndex('user_id', 'user_id');
          store.createIndex('region_name', 'region_name');
          store.createIndex('created_at', 'created_at');
          store.createIndex('synced', 'synced_to_server');
        }
        
        if (!db.objectStoreNames.contains('satellite_cache')) {
          const store = db.createObjectStore('satellite_cache', { keyPath: 'id' });
          store.createIndex('tile_id', 'tile_id');
          store.createIndex('acquisition_date', 'acquisition_date');
        }
        
        if (!db.objectStoreNames.contains('preferences')) {
          db.createObjectStore('preferences', { keyPath: 'key' });
        }
        
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
  await storage.queueSync('analyses', analysis.id, 'insert', encrypted);
  
  // Trigger background sync
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    const reg = await navigator.serviceWorker.ready;
    await reg.sync.register('sync-analyses');
  }
}
"""

(ROOT / "05_INDEXEDDB_CLIENT.js").write_text(indexeddb_client, encoding="utf-8")
print("Created: 05_INDEXEDDB_CLIENT.js")


# ============================================================================
# 4. Server Endpoint (Minimal FastAPI)
# ============================================================================

server_endpoint = """\"\"\"
Minimal Server Endpoint for Local-First Sync
============================================

فقط:
- Auth (login/register/refresh)
- Encrypted blob sync (server cannot read contents)
- Anonymous telemetry

Deployment: Supabase Edge Functions / Cloudflare Workers (NO DOCKER)
\"\"\"
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

app = FastAPI(title="Hydroma Local-First Sync Server")


# ============================================================================
# Models
# ============================================================================

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=12)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_in: int
    subscription_tier: str


class SyncChange(BaseModel):
    id: str
    table: str
    operation: str
    encrypted_payload: str
    iv: str
    lamport_clock: int


class SyncPushRequest(BaseModel):
    changes: List[SyncChange]


# ============================================================================
# Endpoints
# ============================================================================

@app.post("/api/v1/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    \"\"\"Register new user. Server stores only bcrypt hashes.\"\"\"
    return AuthResponse(
        user_id=str(uuid.uuid4()),
        access_token="mock.access.token",
        refresh_token="mock.refresh.token",
        expires_in=3600,
        subscription_tier="free",
    )


@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    \"\"\"Login. Server validates password hash only.\"\"\"
    return AuthResponse(
        user_id="mock-user-id",
        access_token="mock.access.token",
        refresh_token="mock.refresh.token",
        expires_in=3600,
        subscription_tier="free",
    )


@app.post("/api/v1/sync/push")
async def sync_push(
    req: SyncPushRequest,
    authorization: str = Header(...),
):
    \"\"\"
    Accept encrypted changes from client.
    Server CANNOT read the encrypted_payload.
    \"\"\"
    accepted = []
    for change in req.changes:
        # Store encrypted blob in PostgreSQL (BYTEA column)
        # We only store: id, user_id, encrypted_payload, iv, timestamp
        # We DO NOT know what's inside
        accepted.append(change.id)
    
    return {
        "accepted": accepted,
        "rejected": [],
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/sync/pull")
async def sync_pull(
    since: str,
    authorization: str = Header(...),
):
    \"\"\"
    Return encrypted changes since timestamp.
    Client decrypts locally.
    \"\"\"
    return {
        "changes": [],
        "server_time": datetime.now(timezone.utc).isoformat(),
        "vector_clock": {},
    }


@app.post("/api/v1/telemetry")
async def post_telemetry(
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None,
    country_code: Optional[str] = None,
):
    \"\"\"Anonymous telemetry. NO user ID stored.\"\"\"
    return {"received": True}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "mode": "local-first-sync"}
"""

(ROOT / "07_SERVER_ENDPOINT.py").write_text(server_endpoint, encoding="utf-8")
print("Created: 07_SERVER_ENDPOINT.py")


# ============================================================================
# Summary
# ============================================================================

print()
print("=" * 70)
print("Phase 16b: Code files created")
print("=" * 70)
print(f"Location: {ROOT}")
print()
print("All files in local_first/:")
for f in sorted(ROOT.iterdir()):
    size_kb = f.stat().st_size / 1024
    print(f"  - {f.name} ({size_kb:.1f} KB)")
print()
print("=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("""
1. Review all docs:
   Get-ChildItem docs\\architecture\\local_first\\

2. Commit:
   python sandbox\\git_fix.py

3. Decide implementation path:
   - Web PWA (React + IndexedDB + WASM)
   - Mobile (React Native + SQLite)
   - Desktop (Tauri + SQLite)

4. Phase 17: Implement client-side storage
5. Phase 18: Build PWA
6. Phase 19: WASM integration for C++ models
7. Phase 20: Deploy to Supabase + Cloudflare (NO DOCKER)
""")