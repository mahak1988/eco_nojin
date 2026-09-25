import Dexie, { type Table } from 'dexie';

export type OfflineDraft = {
  id: string;
  kind: 'public-form' | 'tool-input';
  payload: Record<string, unknown>;
  updatedAt: number;
};

export type OfflineOutboxEntry = {
  id?: number;
  kind: 'public-form';
  path: string;
  body: string;
  createdAt: number;
  attempts: number;
};

class EcoNojinOfflineDatabase extends Dexie {
  drafts!: Table<OfflineDraft, string>;
  outbox!: Table<OfflineOutboxEntry, number>;

  constructor() {
    super('eco-nojin-offline');
    this.version(1).stores({
      drafts: 'id, updatedAt',
      outbox: '++id, createdAt, kind',
    });
  }
}

export const offlineDb = new EcoNojinOfflineDatabase();
