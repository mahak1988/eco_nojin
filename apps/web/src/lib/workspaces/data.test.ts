import { describe, expect, it } from 'vitest';

import {
  formatTimestamp,
  readAuditEvents,
  readContentHits,
  readDocuments,
  readHealthDetail,
  readHealthState,
  readOrganizations,
  readSyncState,
} from './data';

describe('organization projection', () => {
  it('keeps only the fields the gateway returns', () => {
    const rows = readOrganizations({
      count: 1,
      organizations: [
        {
          id: 'org-1',
          name: 'Cooperative',
          slug: 'cooperative',
          country: 'IR',
          description: 'ignored',
          role: 'admin',
          created_at: '2026-09-01T00:00:00Z',
        },
      ],
    });

    expect(rows).toEqual([
      {
        id: 'org-1',
        name: 'Cooperative',
        slug: 'cooperative',
        country: 'IR',
        membershipRole: 'admin',
        createdAt: '2026-09-01T00:00:00Z',
      },
    ]);
    expect(Object.keys(rows[0])).not.toContain('description');
  });

  it('yields no row for a payload that does not match the contract', () => {
    expect(readOrganizations(null)).toEqual([]);
    expect(readOrganizations({ organizations: 'nope' })).toEqual([]);
    expect(readOrganizations({ organizations: [{ id: 'org-1' }], count: 1 })).toEqual([]);
  });
});

describe('document projection', () => {
  it('lists published documents only', () => {
    const rows = readDocuments({
      count: 2,
      legal_texts: [
        { id: '1', locale: 'fa', slug: 'terms', title: 'Terms', version: 2, status: 'published' },
        { id: '2', locale: 'fa', slug: 'draft', title: 'Draft', version: 1, status: 'draft' },
      ],
    });

    expect(rows).toHaveLength(1);
    expect(rows[0].slug).toBe('terms');
    expect(rows[0].effectiveAt).toBeNull();
  });

  it('yields no row for an unrecognised payload', () => {
    expect(readDocuments({ legal_texts: [], count: 0 })).toEqual([]);
    expect(readDocuments(undefined)).toEqual([]);
  });
});

describe('content search projection', () => {
  it('drops the body snippet the gateway returns', () => {
    const rows = readContentHits({
      query: 'soil',
      count: 1,
      results: [
        {
          id: 'c-1',
          title: 'Soil guide',
          category: 'guide',
          language: 'en',
          published_at: '2026-08-01T00:00:00Z',
          snippet: 'unbounded document text',
        },
      ],
    });

    expect(rows).toEqual([
      {
        id: 'c-1',
        title: 'Soil guide',
        category: 'guide',
        language: 'en',
        publishedAt: '2026-08-01T00:00:00Z',
      },
    ]);
    expect(JSON.stringify(rows)).not.toContain('unbounded document text');
  });
});

describe('audit event projection', () => {
  const payload = {
    status: 'ok',
    events: [
      {
        kind: 'authz',
        ts: 1_788_000_000,
        ip: '203.0.113.7',
        actor: 'user@example.org',
        action: 'role.denied',
        decision: 'deny',
        detail: { path: '/api/v1/organizations' },
        severity: 'warn',
      },
    ],
  };

  it('keeps the non-personal fields and never the personal ones', () => {
    const rows = readAuditEvents(payload);

    expect(rows).toHaveLength(1);
    expect(rows[0].action).toBe('role.denied');
    expect(rows[0].decision).toBe('deny');
    expect(rows[0].severity).toBe('warn');
    expect(rows[0].kind).toBe('authz');
    const serialised = JSON.stringify(rows);
    expect(serialised).not.toContain('203.0.113.7');
    expect(serialised).not.toContain('user@example.org');
    expect(serialised).not.toContain('/api/v1/organizations');
  });

  it('never defaults a missing field into a plausible value', () => {
    const rows = readAuditEvents({
      status: 'ok',
      events: [{ ts: 1_788_000_000, action: 'a', decision: 'allow' }],
    });

    expect(rows[0].kind).toBe('');
    expect(rows[0].severity).toBe('');
    expect(rows[0].occurredAt).toBe('2026-08-29T10:40:00.000Z');
  });

  it('drops an event that does not carry the audit fields', () => {
    const rows = readAuditEvents({ status: 'ok', events: [{ note: 'x' }] });
    expect(rows).toEqual([]);
    expect(readAuditEvents({ status: 'ok' })).toEqual([]);
    expect(readAuditEvents('not json')).toEqual([]);
  });

  it('accepts a millisecond timestamp as well as a second timestamp', () => {
    const rows = readAuditEvents({
      status: 'ok',
      events: [{ ts: '2026-09-25T00:00:00Z', action: 'a', decision: 'allow' }],
    });
    expect(rows[0].occurredAt).toBe('2026-09-25T00:00:00Z');
  });
});

describe('health projection', () => {
  it('reports a degraded payload as unavailable', () => {
    expect(readHealthState({ status: 'degraded' })).toBe('unavailable');
    expect(readHealthState({ status: 'operational' })).toBe('live');
    expect(readHealthState({ available: false })).toBe('unavailable');
    expect(readHealthState({ available: true })).toBe('live');
    expect(readHealthState({ db_reachable: false })).toBe('unavailable');
    expect(readHealthState({ active: false })).toBe('unavailable');
  });

  it('never calls an unreadable payload healthy', () => {
    expect(readHealthState({})).toBe('unavailable');
    expect(readHealthState(null)).toBe('unavailable');
    expect(readHealthState('ok')).toBe('unavailable');
  });

  it('reports only locale-neutral facts as detail', () => {
    expect(readHealthDetail({ status: 'operational', db_backend: 'sqlite' })).toBe(
      'status=operational · db_backend=sqlite',
    );
    expect(readHealthDetail({ status: 'operational', note: 'سلام' })).toBe('status=operational');
  });
});

describe('sync status projection', () => {
  it('reads the registered sync payload', () => {
    expect(
      readSyncState({
        status: 'disabled',
        mode: 'local-first',
        cloud: 'supabase',
        local_pending_events: 0,
        supabase_connected: false,
        supabase_error: 'flag',
      }),
    ).toEqual({
      status: 'disabled',
      mode: 'local-first',
      cloud: 'supabase',
      pendingEvents: 0,
      cloudConnected: false,
    });
  });

  it('returns null when the payload does not match', () => {
    expect(readSyncState({ unexpected: true })).toBeNull();
    expect(readSyncState(null)).toBeNull();
  });
});

describe('timestamp formatting', () => {
  it('reports a missing or invalid value as not provided', () => {
    expect(formatTimestamp(null, 'en', 'not provided')).toBe('not provided');
    expect(formatTimestamp('', 'en', 'not provided')).toBe('not provided');
    expect(formatTimestamp('not a date', 'en', 'not provided')).toBe('not provided');
  });

  it('formats a real timestamp for the locale', () => {
    expect(formatTimestamp('2026-09-25T00:00:00Z', 'en', 'not provided')).toContain('2026');
  });
});
