import { randomBytes } from 'node:crypto';
import { createClient } from 'redis';
import { getRedisUrl, getSessionTtlSeconds } from '@/lib/config/server-env';
import type { SessionRecord } from './session-cookie';

type RedisSessionClient = {
  isOpen: boolean;
  connect: () => Promise<unknown>;
  on: (event: string, listener: () => void) => unknown;
  get: (key: string) => Promise<string | null>;
  set: (key: string, value: string, options: { EX: number }) => Promise<unknown>;
  del: (key: string) => Promise<unknown>;
};

const keyPrefix = 'eco:session:';
let redisPromise: Promise<RedisSessionClient | null> | null = null;

type MemorySession = { record: SessionRecord; expiresAt: number };
const globalStore = globalThis as typeof globalThis & {
  __ecoSessionMemory?: Map<string, MemorySession>;
};
const memory = globalStore.__ecoSessionMemory ?? new Map<string, MemorySession>();
globalStore.__ecoSessionMemory = memory;

async function redisClient() {
  const url = getRedisUrl();
  if (!url) return null;
  if (!redisPromise) {
    redisPromise = (async () => {
      const client = createClient({ url }) as unknown as RedisSessionClient;
      client.on('error', () => undefined);
      if (!client.isOpen) await client.connect();
      return client;
    })();
  }
  return redisPromise;
}

function key(id: string): string {
  return `${keyPrefix}${id}`;
}

function readMemory(id: string): SessionRecord | null {
  const entry = memory.get(id);
  if (!entry) return null;
  if (entry.expiresAt <= Date.now()) {
    memory.delete(id);
    return null;
  }
  return entry.record;
}

export async function createStoredSession(record: SessionRecord): Promise<string> {
  const id = randomBytes(32).toString('base64url');
  const client = await redisClient();
  if (client) {
    await client.set(key(id), JSON.stringify(record), { EX: getSessionTtlSeconds() });
    return id;
  }
  memory.set(id, { record, expiresAt: Date.now() + getSessionTtlSeconds() * 1000 });
  return id;
}

export async function getStoredSession(id: string): Promise<SessionRecord | null> {
  const client = await redisClient();
  if (client) {
    const value = await client.get(key(id));
    return value ? (JSON.parse(value) as SessionRecord) : null;
  }
  return readMemory(id);
}

export async function replaceStoredSession(id: string, record: SessionRecord): Promise<void> {
  const client = await redisClient();
  if (client) {
    await client.set(key(id), JSON.stringify(record), { EX: getSessionTtlSeconds() });
    return;
  }
  memory.set(id, { record, expiresAt: Date.now() + getSessionTtlSeconds() * 1000 });
}

export async function deleteStoredSession(id: string): Promise<void> {
  const client = await redisClient();
  if (client) {
    await client.del(key(id));
    return;
  }
  memory.delete(id);
}
