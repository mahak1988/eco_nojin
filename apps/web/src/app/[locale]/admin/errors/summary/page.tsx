import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';

import { ledgerCopy } from '../../_lib/copy';
import { LedgerSurface, RecordList, resolveLedgerState, scalar } from '../../_lib/surface';

const SLUG = 'admin-admin-errors-summary';
const ROUTE = '/admin/errors/summary';
const PATH = '/api/v1/admin/errors/summary';

/**
 * `GET /api/v1/admin/errors/summary` — `services/api_gateway/routers/admin_errors.py:142`.
 *
 * The handler returns the counts and the two breakdowns of `ERROR_STORE` and
 * declares no `response_model`, so the published schema is an untyped object.
 * The fields it computes are `total`, `by_severity`, `by_type`, `by_status` and
 * `recent` (`admin_errors.py:148-158`).
 *
 * This route is currently unreachable as written. `admin_errors.py:83` registers
 * `@router.get("/{error_id}")` *before* `:142` registers `@router.get("/summary")`,
 * and Starlette matches in registration order, so `GET /api/v1/admin/errors/summary`
 * is routed to the record lookup with `error_id="summary"`, which finds nothing in
 * `ERROR_STORE` and raises `404 "Error not found"` (`admin_errors.py:95-96`).
 * Both paths appear in the OpenAPI document, so the catalogue is right that the
 * contract exists; it is the router's declaration order that is wrong.
 *
 * The page is built to the contract as declared and renders the `error` state
 * naming the path, which is the truth today. It is not special-cased to
 * reproduce the routing bug in prose: when the order is fixed upstream this page
 * starts working with no change here, and copy that asserted a defect could not
 * be corrected from the frontend.
 */
interface SummaryPayload {
  total?: number;
  by_severity?: Record<string, number>;
  by_type?: Record<string, number>;
  by_status?: Record<string, number>;
  recent?: unknown[];
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
      url: `${BASE_URL}/${locale}${ROUTE}`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('admin');

  const result = await adminGet<SummaryPayload>(adminToken(await readAdminSession()), PATH);
  const payload = result.ok ? (result.data ?? {}) : {};
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="admin"
      title={meta('title')}
      description={meta('description')}
      path={PATH}
      slug={SLUG}
      state={state}
      total={result.ok ? 1 : 0}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={result.ok ? undefined : `${PATH} · ${result.status}`}
      data={
        result.ok ? (
          <RecordList
            caption={meta('title')}
            fields={[
              { label: c.total, value: scalar(payload.total) },
              { label: c.status, value: scalar(payload.by_severity) },
              { label: c.type, value: scalar(payload.by_type) },
              { label: c.group, value: scalar(payload.by_status) },
              { label: c.count, value: scalar((payload.recent ?? []).length) },
            ]}
          />
        ) : null
      }
      detail={
        <p className="text-xs text-ink-soft">
          {copy.processMemory} <span className="num">{PATH}</span>
        </p>
      }
    />
  );
}
