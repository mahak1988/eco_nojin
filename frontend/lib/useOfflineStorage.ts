/**
 * Offline Storage Hook using IndexedDB
 *
 * Uses deferred client state pattern to avoid hydration mismatches.
 * isOnline starts as null (not mounted), only set to actual value after mount.
 */
import { useState, useEffect, useCallback } from 'react';
import { API_BASE } from './config';

const DB_NAME = 'eco-nojin-offline';
const DB_VERSION = 1;
const STORE_NAME = 'offline-queue';

interface QueuedItem {
  id: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'DELETE';
  payload: any;
  timestamp: number;
  retryCount: number;
  status: 'pending' | 'syncing' | 'failed';
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB not available'));
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        store.createIndex('status', 'status', { unique: false });
        store.createIndex('timestamp', 'timestamp', { unique: false });
      }
    };
  });
}

export function useOfflineStorage() {
  // CRITICAL: Start as null to avoid SSR/client mismatch
  const [queueSize, setQueueSize] = useState<number>(0);
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  // Set online status ONLY after component mounts (client-side)
  useEffect(() => {
    if (typeof navigator === 'undefined') return;

    // Set initial value after mount
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Update queue size periodically (only after mount)
  useEffect(() => {
    let cancelled = false;

    const updateSize = async () => {
      try {
        const db = await openDB();
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const count = await new Promise<number>((resolve) => {
          const request = store.count();
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => resolve(0);
        });
        if (!cancelled) setQueueSize(count);
        db.close();
      } catch {
        // IndexedDB not available - ignore
      }
    };

    updateSize();
    const interval = setInterval(updateSize, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const addToQueue = useCallback(async (
    endpoint: string,
    method: 'POST' | 'PUT' | 'DELETE',
    payload: any
  ): Promise<string> => {
    const id = `q_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const item: QueuedItem = {
      id,
      endpoint,
      method,
      payload,
      timestamp: Date.now(),
      retryCount: 0,
      status: 'pending',
    };

    try {
      const db = await openDB();
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      await new Promise<void>((resolve, reject) => {
        const request = store.add(item);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
      db.close();
      setQueueSize((prev) => prev + 1);
    } catch {
      // IndexedDB not available
    }
    return id;
  }, []);

  const processQueue = useCallback(async (): Promise<{
    synced: number;
    failed: number;
  }> => {
    if (typeof navigator === 'undefined' || !navigator.onLine) {
      return { synced: 0, failed: 0 };
    }

    try {
      const db = await openDB();
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);

      const pendingItems = await new Promise<QueuedItem[]>((resolve) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result || []);
        request.onerror = () => resolve([]);
      });

      let synced = 0;
      let failed = 0;

      for (const item of pendingItems) {
        if (item.status === 'syncing') continue;

        item.status = 'syncing';
        store.put(item);

        try {
          const response = await fetch(`${API_BASE}${item.endpoint}`, {
            method: item.method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(item.payload),
          });

          if (response.ok) {
            store.delete(item.id);
            synced++;
          } else if (item.retryCount < 3) {
            item.retryCount++;
            item.status = 'pending';
            store.put(item);
            failed++;
          } else {
            item.status = 'failed';
            store.put(item);
            failed++;
          }
        } catch {
          item.status = 'pending';
          item.retryCount++;
          store.put(item);
          failed++;
        }
      }

      db.close();
      setQueueSize((prev) => Math.max(0, prev - synced));

      return { synced, failed };
    } catch {
      return { synced: 0, failed: 0 };
    }
  }, []);

  const clearQueue = useCallback(async (): Promise<void> => {
    try {
      const db = await openDB();
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      await new Promise<void>((resolve) => {
        const request = store.clear();
        request.onsuccess = () => resolve();
      });
      db.close();
      setQueueSize(0);
    } catch {
      // Ignore
    }
  }, []);

  return {
    queueSize,
    isOnline,  // Now null | boolean (null = not yet mounted)
    addToQueue,
    processQueue,
    clearQueue,
  };
}
