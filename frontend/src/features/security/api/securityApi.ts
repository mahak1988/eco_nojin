/**
 * Security API
 * =============
 * @module features/security/api
 */

import type { SecurityEvent, RawSecurityEvent } from '../types';
import { ENDPOINTS } from '../constants/config';

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('access_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Transform raw API event to typed SecurityEvent.
 * Moved from component to API layer (proper separation).
 */
function transformEvent(raw: RawSecurityEvent, index: number): SecurityEvent {
  const detail = raw.detail || '';
  const isFailed = detail.toLowerCase().startsWith('failed');

  return {
    id: (raw.id as string) || `evt-${index}`,
    type: isFailed
      ? 'Failed Login'
      : isFailed === false && detail
        ? 'Successful Login'
        : 'Successful Login',
    detail,
    ip_address: (raw.ip_address as string) || '',
    created_at: (raw.created_at as string) || '',
    severity: isFailed ? 'high' : 'low',
  };
}

/**
 * Fetch security events with transformation.
 */
export async function fetchSecurityEvents(): Promise<SecurityEvent[]> {
  const response = await fetch(ENDPOINTS.security, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const json = await response.json();
  const rawEvents = (json.events || []) as RawSecurityEvent[];
  return rawEvents.map(transformEvent);
}
