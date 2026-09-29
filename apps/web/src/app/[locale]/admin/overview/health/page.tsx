import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

import { ledgerCopy } from '../../_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  PlaceholderNotice,
  PREVIEW_LIMIT,
  readRows,
  resolveLedgerState,
  scalar,
  UnmeasuredCell,
} from '../../_lib/surface';

const SLUG = 'admin-admin-overview-health';
const ROUTE = '/admin/overview/health';
const PATH = '/api/v1/admin/overview/health';

/**
 * `GET /api/v1/admin/overview/health` —
 * `services/api_gateway/routers/admin_overview.py:81`.
 *
 * `response_model=List[ChannelHealth]`, so the payload is a bare array.
 * `ChannelHealth` is declared at `admin_overview.py:25` with `name`, `status`,
 * `latency_ms` and `last_check`.
 *
 * ## Every value in this payload is fabricated
 *
 * `admin_overview.py:88-97` returns a literal list of four rows. Each row's
 * `status` is the string `"healthy"` — not a result of a probe, and not
 * conditional on anything — and each `latency_ms` is a chosen constant
 * (45.2, 12.1, 8.3, 3.7). `last_check` is `datetime.now()`, so it records when
 * the response was built, not when anything was checked; the gateway contacts no
 * channel on this path.
 *
 * The brief named this endpoint, and the choice made here is to withhold the
 * numbers rather than to footnote them. A table of four green ticks and three
 * one-decimal latencies is indistinguishable, to anyone who has not read the
 * router, from a real health matrix — a footnote is the only thing separating
 * them and a footnote is exactly what gets dropped when a table is screenshotted
 * into an incident channel. So the page renders the two fields that are not
 * invented (`name`, which is also the row identity, and `last_check`, labelled as
 * the response time), labels `status` and `latency_ms` as not measured, and puts
 * the reason above the table.
 *
 * `components/admin/admin-sections.ts:104-113` reaches the same conclusion for
 * this capability and refuses it outright: `endpoint: null`, gap "returns a
 * hard-coded channel list".
 */
interface ChannelRow {
  name?: string;
  status?: string;
  latency_ms?: number;
  last_check?: string;
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

  const result = await adminGet<ChannelRow[]>(adminToken(await readAdminSession()), PATH);
  const rows = readRows<ChannelRow>(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, rows.length);
  const visible = rows.slice(0, PREVIEW_LIMIT);
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
      total={rows.length}
      ok={result.ok}
      stateDetail={`${PATH} · ${rows.length}`}
      data={
        <div className="flex flex-col gap-3">
          <PlaceholderNotice heading={copy.placeholderHeading} body={copy.placeholderBody} />
          <LedgerTable<ChannelRow>
            columns={[
              { key: 'name', header: c.name, render: (row) => scalar(row.name) },
              {
                key: 'status',
                header: c.status,
                render: () => <UnmeasuredCell label={copy.notMeasured} />,
              },
              {
                key: 'latency',
                header: c.value,
                render: () => <UnmeasuredCell label={copy.notMeasured} />,
              },
              { key: 'last_check', header: c.updated, render: (row) => scalar(row.last_check) },
            ]}
            rows={visible}
            rowKey={(row) => String(row.name ?? '')}
            caption={meta('title')}
            emptyLabel={copy.emptyLabel}
          />
        </div>
      }
      detail={
        <p className="num text-xs text-ink-faint">
          {PATH} — services/api_gateway/routers/admin_overview.py:88
        </p>
      }
    />
  );
}
