import { z } from 'zod';

/**
 * Runtime projections for every payload the workspace is allowed to read.
 *
 * Three rules are enforced here rather than in the components:
 *
 * 1. Nothing is invented. A field the gateway did not send is dropped, never
 *    defaulted, and a payload that does not match its contract yields zero rows
 *    instead of a plausible one.
 * 2. Personal data is withheld unless the backend declares a scope for it. The
 *    security event stream carries an actor, an IP address and a free-form detail
 *    blob; the response declares no scope, so only the non-personal projection is
 *    ever built.
 * 3. The session identity is only ever read from the server record, never from
 *    browser storage.
 */

const organizationSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  slug: z.string().min(1),
  country: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  role: z.string().min(1),
  created_at: z.string().nullable().optional(),
});

const organizationListSchema = z.object({
  organizations: z.array(organizationSchema),
  count: z.number().int().nonnegative(),
});

export interface WorkspaceOrganization {
  id: string;
  name: string;
  slug: string;
  country: string | null;
  membershipRole: string;
  createdAt: string | null;
}

export function readOrganizations(payload: unknown): WorkspaceOrganization[] {
  const parsed = organizationListSchema.safeParse(payload);
  if (!parsed.success) return [];
  return parsed.data.organizations.map((organization) => ({
    id: organization.id,
    name: organization.name,
    slug: organization.slug,
    country: organization.country ?? null,
    membershipRole: organization.role,
    createdAt: organization.created_at ?? null,
  }));
}

const legalTextSchema = z.object({
  id: z.string().min(1),
  locale: z.string().min(1),
  slug: z.string().min(1),
  title: z.string().min(1),
  version: z.number().int().positive(),
  status: z.string().min(1),
  effective_at: z.string().nullable().optional(),
  updated_at: z.string().nullable().optional(),
});

const legalTextListSchema = z.object({
  legal_texts: z.array(legalTextSchema),
  count: z.number().int().nonnegative(),
});

export interface WorkspaceDocument {
  id: string;
  locale: string;
  slug: string;
  title: string;
  version: number;
  status: string;
  effectiveAt: string | null;
  updatedAt: string | null;
}

/** Published documents only; a draft or archived record is never listed here. */
export function readDocuments(payload: unknown): WorkspaceDocument[] {
  const parsed = legalTextListSchema.safeParse(payload);
  if (!parsed.success) return [];
  return parsed.data.legal_texts
    .filter((document) => document.status === 'published')
    .map((document) => ({
      id: document.id,
      locale: document.locale,
      slug: document.slug,
      title: document.title,
      version: document.version,
      status: document.status,
      effectiveAt: document.effective_at ?? null,
      updatedAt: document.updated_at ?? null,
    }));
}

const contentSearchSchema = z.object({
  query: z.string(),
  count: z.number().int().nonnegative(),
  results: z.array(
    z.object({
      id: z.string().min(1),
      title: z.string().min(1),
      category: z.string().nullable().optional(),
      language: z.string().nullable().optional(),
      published_at: z.string().nullable().optional(),
    }),
  ),
});

export interface WorkspaceContentHit {
  id: string;
  title: string;
  category: string | null;
  language: string | null;
  publishedAt: string | null;
}

/**
 * The body snippet the gateway returns is deliberately not projected: a search
 * result excerpt is unbounded document text and is not needed to identify a hit.
 */
export function readContentHits(payload: unknown): WorkspaceContentHit[] {
  const parsed = contentSearchSchema.safeParse(payload);
  if (!parsed.success) return [];
  return parsed.data.results.map((hit) => ({
    id: hit.id,
    title: hit.title,
    category: hit.category ?? null,
    language: hit.language ?? null,
    publishedAt: hit.published_at ?? null,
  }));
}

const securityEventSchema = z.object({
  ts: z.union([z.number(), z.string()]),
  kind: z.string().min(1).optional(),
  action: z.string().min(1),
  decision: z.string().min(1),
  severity: z.string().min(1).optional(),
});

const securityEventListSchema = z.object({
  status: z.string(),
  events: z.array(z.unknown()),
});

export interface WorkspaceAuditEvent {
  id: string;
  occurredAt: string;
  kind: string;
  action: string;
  decision: string;
  severity: string;
}

/**
 * Non-personal projection of a backend-produced security event.
 *
 * `actor`, `ip` and `detail` exist in the payload and are intentionally not
 * read here: the endpoint declares no scope for personal data, so the workspace
 * reports that a richer field set exists without displaying any of it.
 */
export function readAuditEvents(payload: unknown): WorkspaceAuditEvent[] {
  const parsed = securityEventListSchema.safeParse(payload);
  if (!parsed.success) return [];
  const rows: WorkspaceAuditEvent[] = [];
  parsed.data.events.forEach((event, index) => {
    const record = securityEventSchema.safeParse(event);
    if (!record.success) return;
    const occurredAt =
      typeof record.data.ts === 'number'
        ? new Date(record.data.ts * 1000).toISOString()
        : record.data.ts;
    rows.push({
      id: `${record.data.action}-${record.data.decision}-${index}`,
      occurredAt,
      kind: record.data.kind ?? '',
      action: record.data.action,
      decision: record.data.decision,
      severity: record.data.severity ?? '',
    });
  });
  return rows;
}

const healthSchema = z
  .object({
    status: z.string().optional(),
    available: z.boolean().optional(),
    db_reachable: z.boolean().optional(),
    active: z.boolean().optional(),
    note: z.string().optional(),
    db_backend: z.string().optional(),
    mode: z.string().optional(),
  })
  .passthrough();

export type WorkspaceHealthState = 'live' | 'unavailable';

/**
 * A 200 response is not proof of health. A payload that reports `degraded`,
 * `available: false`, an unreachable database or a disabled feature is reported
 * as unavailable, and an unreadable payload is never called live.
 */
export function readHealthState(payload: unknown): WorkspaceHealthState {
  const parsed = healthSchema.safeParse(payload);
  if (!parsed.success) return 'unavailable';
  const record = parsed.data;
  if (typeof record.status === 'string') {
    return ['operational', 'ok', 'healthy', 'live'].includes(record.status.toLowerCase())
      ? 'live'
      : 'unavailable';
  }
  if (record.available === false) return 'unavailable';
  if (record.db_reachable === false) return 'unavailable';
  if (record.active === false) return 'unavailable';
  if (record.status === undefined && record.available === undefined) return 'unavailable';
  return 'live';
}

/** Locale-neutral facts worth showing next to a health probe. */
export function readHealthDetail(payload: unknown): string {
  const parsed = healthSchema.safeParse(payload);
  if (!parsed.success) return '';
  const parts: string[] = [];
  for (const key of ['status', 'mode', 'db_backend'] as const) {
    const value = parsed.data[key];
    if (typeof value === 'string' && value !== '') parts.push(`${key}=${value}`);
  }
  return parts.join(' · ');
}

const syncStatusSchema = z
  .object({
    status: z.string().optional(),
    mode: z.string().nullable().optional(),
    cloud: z.string().nullable().optional(),
    local_pending_events: z.number().int().nonnegative().nullable().optional(),
    supabase_connected: z.boolean().nullable().optional(),
  })
  .passthrough();

export interface WorkspaceSyncState {
  status: string | null;
  mode: string | null;
  cloud: string | null;
  pendingEvents: number | null;
  cloudConnected: boolean | null;
}

export function readSyncState(payload: unknown): WorkspaceSyncState | null {
  const parsed = syncStatusSchema.safeParse(payload);
  if (!parsed.success) return null;
  // A payload that carries none of the known fields is not a reading: reporting
  // an all-null state would look like a real measurement of a disabled service.
  const known = [
    parsed.data.status,
    parsed.data.mode,
    parsed.data.cloud,
    parsed.data.local_pending_events,
    parsed.data.supabase_connected,
  ];
  if (known.every((value) => value === undefined)) return null;
  return {
    status: parsed.data.status ?? null,
    mode: parsed.data.mode ?? null,
    cloud: parsed.data.cloud ?? null,
    pendingEvents: parsed.data.local_pending_events ?? null,
    cloudConnected: parsed.data.supabase_connected ?? null,
  };
}

/** A date rendered for the reader, or an explicit "not provided" marker. */
export function formatTimestamp(value: string | null, locale: string, notProvided: string): string {
  if (value === null || value === '') return notProvided;
  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) return notProvided;
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
    parsedDate,
  );
}
