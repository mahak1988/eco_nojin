/** Status API client — service health, freeze, retirement, idempotency.
 * Health polling hits real gateway endpoint; other data is simulation/pre-verification. */

import { getApiBase } from './api';
import type {
  HealthStatus,
  FreezeStatus,
  RetirementStatus,
  IdempotencyStatus,
  StatusSummary,
} from '../types/status';

const apiBase = getApiBase();

async function statusFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  const token = localStorage.getItem('hydroma_token');
  if (token && !options?.skipAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail || `status_error_${res.status}`);
  }
  return res.json() as T;
}

/** Probes the real gateway /health endpoint (live check). */
export async function probeHealth(): Promise<HealthStatus> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(`${apiBase}/health`, {
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!response.ok) {
      throw new Error(`health_check_failed_${response.status}`);
    }
    return response.json() as HealthStatus;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

/** Fetches freeze status — simulation indicator. */
export async function fetchFreezeStatus(accountId: string): Promise<FreezeStatus> {
  return statusFetch<FreezeStatus>(`/api/v1/status/freeze/${accountId}`);
}

/** Fetches retirement status — simulation indicator. */
export async function fetchRetirementStatus(creditId: string): Promise<RetirementStatus> {
  return statusFetch<RetirementStatus>(`/api/v1/status/retirement/${creditId}`);
}

/** Lists idempotency keys for a user. */
export async function fetchIdempotencyStatus(params?: {
  userId?: string;
  status?: string;
  limit?: number;
}): Promise<IdempotencyStatus[]> {
  const qs = new URLSearchParams();
  if (params?.userId) qs.set('userId', params.userId);
  if (params?.status) qs.set('status', params.status);
  if (params?.limit) qs.set('limit', String(params.limit));
  const q = qs.toString();
  return statusFetch<IdempotencyStatus[]>(
    `/api/v1/status/idempotency${q ? `?${q}` : ''}`,
  );
}

/** Fetches full status summary — simulation + live health probe. */
export async function fetchStatusSummary(): Promise<StatusSummary> {
  return statusFetch<StatusSummary>('/api/v1/status/summary');
}
