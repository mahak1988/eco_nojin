// client-storage.js
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
