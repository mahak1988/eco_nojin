/**
 * ContentStudio Configuration
 * ==============================
 * @module features/content-studio/constants
 */

import type { ContentFilter } from '../types';

/** API base URL */
export const API_BASE =
  (typeof import.meta !== 'undefined' &&
    (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env
      ?.VITE_API_BASE) ||
  'http://localhost:8000/api/v1';

/** API endpoints */
export const ENDPOINTS = {
  content: `${API_BASE}/admin/content`,
  publish: (id: string) => `${API_BASE}/admin/content/${id}/publish`,
  delete: (id: string) => `${API_BASE}/admin/content/${id}`,
  generateDraft: `${API_BASE}/admin/content/generate-draft`,
  translate: (id: string) => `${API_BASE}/admin/content/${id}/translate`,
} as const;

/** React Query keys */
export const QUERY_KEYS = {
  content: ['content-studio', 'items'] as const,
} as const;

/** Filter options */
export const FILTER_OPTIONS: ContentFilter[] = [
  'all',
  'published',
  'draft',
  'scheduled',
];

/** Default generate draft topic */
export const DEFAULT_TOPIC = 'Sustainable Farming';

/** Default language */
export const DEFAULT_LANGUAGE = 'fa';

/** Default translation target */
export const DEFAULT_TRANSLATION_TARGET = 'en';

/** React Query stale time (5 minutes) */
export const STALE_TIME_MS = 5 * 60 * 1000;

/** React Query retry count */
export const RETRY_COUNT = 2;
