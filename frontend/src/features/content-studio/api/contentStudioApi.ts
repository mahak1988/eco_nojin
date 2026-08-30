/**
 * ContentStudio API Functions
 * =============================
 * @module features/content-studio/api
 */

import type {
  ContentItem,
  GenerateDraftRequest,
  TranslateRequest,
} from '../types';
import { ENDPOINTS } from '../constants/config';

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('access_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/** Normalize API response */
function normalizeArray<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    const obj = data as { items?: T[] };
    return obj.items || [];
  }
  return [];
}

/** Fetch all content items */
export async function fetchContentItems(): Promise<ContentItem[]> {
  const response = await fetch(ENDPOINTS.content, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch content: ${response.statusText}`);
  }
  const data = await response.json();
  return normalizeArray<ContentItem>(data);
}

/** Publish a content item */
export async function publishContentItem(id: string): Promise<void> {
  const response = await fetch(ENDPOINTS.publish(id), {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to publish: ${response.statusText}`);
  }
}

/** Delete a content item */
export async function deleteContentItem(id: string): Promise<void> {
  const response = await fetch(ENDPOINTS.delete(id), {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Failed to delete: ${response.statusText}`);
  }
}

/** Generate AI draft */
export async function generateDraft(
  request: GenerateDraftRequest
): Promise<ContentItem> {
  const response = await fetch(ENDPOINTS.generateDraft, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to generate draft: ${response.statusText}`);
  }
  return response.json() as Promise<ContentItem>;
}

/** Translate content item */
export async function translateContentItem(
  id: string,
  request: TranslateRequest
): Promise<void> {
  const response = await fetch(ENDPOINTS.translate(id), {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to translate: ${response.statusText}`);
  }
}
