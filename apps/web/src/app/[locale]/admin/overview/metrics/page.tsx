import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

import { ledgerCopy } from '../../_lib/copy';
import { LedgerSurface, PlaceholderNotice, record, resolveLedgerState } from '../../_lib/surface';

const SLUG = 'admin-admin-overview-metrics';
const ROUTE = '/admin/overview/metrics';
const PATH = '/api/v1/admin/overview/metrics';

/**
 * `GET /api/v1/admin/overview/metrics` —
 * `services/api_gateway/routers/admin_overview.py:100`.
 *
 * The handler declares no `response_model`, so the published schema is an untyped
 * object. It returns the `hours` it was asked for plus `requests_per_minute`,
 * `active_users`, `cpu_percent`, `memory_percent` and a `top_endpoints` map
 * (`admin_overview.py:107-116`).
 *
 * ## Nothing in this payload is a measurement
 *
 * `admin_overview.py:105` is a two-line comment — "Mock data - replace with
 * actual metrics collection" — followed by a literal dict. `cpu_percent` is 45.0
 * and `memory_percent` is 62.0 for every window ever requested; `requests_per_minute`
 * is 120.0; and `top_endpoints` invents per-endpoint request counts, which are the
 * numbers an operator would use first and the ones most damaging to be wrong.
 *
 * There is no partial here to keep, so the page renders no figures at all. It
 * states that the contract answered, names the contract, and says that the values
 * it carries are constants — which is the whole finding, and is more use to a
 * reader than a plausible number.
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

  const result: Fetched = await adminGet<Record<string, unknown>>(
    adminToken(await readAdminSession()),
    PATH,
  );
  // A 2xx that carries no measurement is still a successful request, and the
  // page has something true to render: the contract answered and what it answered
  // is a constant. So the state is `ready` and the data region is the notice.
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
  const fields = record(result.ok ? result.data : undefined);

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
      stateDetail={
        result.ok ? `${PATH} · ${Object.keys(fields).length}` : `${PATH} · ${result.status}`
      }
      data={
        result.ok ? (
          <div className="flex flex-col gap-3">
            <PlaceholderNotice heading={copy.placeholderHeading} body={copy.placeholderBody} />
            <p className="num text-xs text-ink-faint">
              {PATH} — services/api_gateway/routers/admin_overview.py:105
            </p>
          </div>
        ) : null
      }
    />
  );
}
