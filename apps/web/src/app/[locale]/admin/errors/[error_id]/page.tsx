import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';

import { ledgerCopy } from '../../_lib/copy';
import {
  LedgerSurface,
  RecordList,
  record,
  resolveLedgerState,
  scalar,
  segment,
} from '../../_lib/surface';

const SLUG = 'admin-admin-errors-error_id';
const ROUTE = '/admin/errors/{error_id}';
const PATH = '/api/v1/admin/errors/{error_id}';

/**
 * `GET /api/v1/admin/errors/{error_id}` —
 * `services/api_gateway/routers/admin_errors.py:83`.
 *
 * `response_model=ErrorResponse`, so the payload is a single record, not a list.
 * `ErrorResponse` is declared at `admin_errors.py:27` with `id`, `timestamp`,
 * `severity`, `error_type`, `message`, `endpoint` and `user_id`. The handler
 * looks the id up in `ERROR_STORE` and raises `404` when it is absent
 * (`admin_errors.py:88-96`).
 *
 * The sibling `/summary` route is registered after this one and is therefore
 * shadowed by it; that is a gateway defect and is reported rather than reproduced
 * here. The path segment is resolved from the route parameter, so the page asks
 * about the record the address names rather than the literal `{error_id}`.
 */
interface Fetched {
  ok: boolean;
  status: number;
  data?: Record<string, unknown>;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/admin/errors`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/admin/errors'),
      languages: languageAlternates('/admin/errors'),
    },
  };
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; error_id: string }>;
}) {
  const { error_id } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('admin');
  const endpoint = PATH.replace('{error_id}', segment(error_id));

  const result: Fetched = await adminGet<Record<string, unknown>>(
    adminToken(await readAdminSession()),
    endpoint,
  );
  const payload = record(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="admin"
      title={meta('title')}
      description={meta('description')}
      path={endpoint}
      slug={SLUG}
      state={state}
      total={result.ok ? 1 : 0}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={result.ok ? undefined : `${endpoint} · ${result.status}`}
      data={
        result.ok ? (
          <RecordList
            caption={meta('title')}
            fields={[
              { label: c.identifier, value: scalar(payload.id) },
              { label: c.created, value: scalar(payload.timestamp) },
              { label: c.status, value: scalar(payload.severity) },
              { label: c.type, value: scalar(payload.error_type) },
              { label: c.source, value: scalar(payload.endpoint) },
              { label: c.message, value: scalar(payload.message) },
              { label: c.member, value: scalar(payload.user_id) },
            ]}
          />
        ) : null
      }
      detail={
        <p className="text-xs text-ink-soft">
          {copy.processMemory} <span className="num">{endpoint}</span>
        </p>
      }
    />
  );
}
