import { isAllowedOfflineMutation } from './cache-policy';
import { type OfflineOutboxEntry, offlineDb } from './db';

export async function queueOfflineMutation(input: {
  path: string;
  body: Record<string, unknown>;
}): Promise<number> {
  if (!isAllowedOfflineMutation(input.path, 'POST')) {
    throw new Error('This mutation is not allowed offline');
  }
  return offlineDb.outbox.add({
    kind: 'public-form',
    path: input.path,
    body: JSON.stringify(input.body),
    createdAt: Date.now(),
    attempts: 0,
  });
}

export async function flushOfflineOutbox(): Promise<number> {
  if (typeof navigator !== 'undefined' && !navigator.onLine) return 0;
  const entries = await offlineDb.outbox.orderBy('createdAt').toArray();
  let flushed = 0;
  for (const entry of entries) {
    if (entry.id === undefined) continue;
    try {
      const response = await fetch(entry.path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Intent': '1' },
        credentials: 'same-origin',
        body: entry.body,
      });
      if (!response.ok) break;
      await offlineDb.outbox.delete(entry.id);
      flushed += 1;
    } catch {
      await offlineDb.outbox.update(entry.id, { attempts: entry.attempts + 1 });
      break;
    }
  }
  return flushed;
}

export async function pendingOfflineMutations(): Promise<OfflineOutboxEntry[]> {
  return offlineDb.outbox.orderBy('createdAt').toArray();
}
