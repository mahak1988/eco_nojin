import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { verificationOf } from '@/lib/api/surfaces';

import { ledgerCopy } from '../_lib/copy';
import {
  LedgerSurface,
  number,
  PlaceholderNotice,
  RecordList,
  record,
  resolveLedgerState,
  UnmeasuredCell,
} from '../_lib/surface';

const SLUG = 'admin-admin-overview';
const ROUTE = '/admin/overview';
const PATH = '/api/v1/admin/overview';

/**
 * `GET /api/v1/admin/overview` — `services/api_gateway/routers/admin_overview.py:41`.
 *
 * `response_model=PlatformStats`, so the payload is one record. `PlatformStats` is
 * declared at `admin_overview.py:15`.
 *
 * ## Seven real counts and five placeholders
 *
 * The first seven fields are counted over the database at `admin_overview.py:47-61`
 * and are real. The remaining five are not: `admin_overview.py:63-66` returns
 * `{"active_users_24h": 0, "revenue_24h": 0}` under the comment
 * "Real data would come from analytics tables", and `admin_overview.py:69-75`
 * returns `api_requests_24h: 0`, `error_rate_24h: 0.0` and
 * `avg_response_time_ms: 0.0` under "# Mock". The page renders the seven counts
 * with their names and labels the five as not measured.
 *
 * One name also lies about a field that *is* real. `active_users_24h` is computed
 * as `db.query(User).filter(User.is_active == True).count()` (`admin_overview.py:57`)
 * — every account flagged active, with no time window anywhere in the query. The
 * page therefore labels that row as the count of active accounts rather than as
 * activity in the last twenty-four hours, because the number is right and the
 * twenty-four hours are not.
 *
 * `components/admin/admin-sections.ts:92-102` records the same decision for this
 * capability — `endpoint: null`, gap "admin_overview.py returns placeholder
 * counters" — but the contract is published and the real half of it is worth
 * showing, so the page reads the contract and withholds only the placeholders.
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
  const payload = record(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
  const c = copy.columns;
  const notMeasured = <UnmeasuredCell label={copy.notMeasured} />;

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
          <div className="flex flex-col gap-3">
            <PlaceholderNotice heading={copy.placeholderHeading} body={copy.placeholderBody} />
            <RecordList
              caption={meta('title')}
              fields={[
                { label: c.member, value: number(payload.total_users) },
                { label: c.count, value: number(payload.total_farms) },
                { label: c.total, value: number(payload.total_land_profiles) },
                { label: c.detail, value: number(payload.total_content) },
                { label: c.status, value: number(payload.published_content) },
                { label: c.value, value: number(payload.total_marketplace_products) },
                { label: c.action, value: number(payload.total_orders) },
                { label: c.group, value: number(payload.active_users_24h) },
                { label: c.amount, value: notMeasured },
                { label: c.source, value: notMeasured },
                { label: c.type, value: notMeasured },
                { label: c.version, value: notMeasured },
              ]}
            />
          </div>
        ) : null
      }
    />
  );
}
