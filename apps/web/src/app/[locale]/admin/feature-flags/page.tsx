import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminDataGrid, type AdminGridColumn } from '@/components/admin/AdminDataGrid';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import {
  AdminCapabilityTable,
  AdminSourceNote,
  AdminUnavailable,
} from '@/components/admin/AdminStates';
import { getAdminSection, REGISTRY_FILE } from '@/components/admin/admin-sections';
import { StatusDot } from '@/components/StatusDot';
import { DOMAIN_ROUTES } from '@/lib/domains/registry';

// The capability matrix is the real registry file, re-read on every request.
export const dynamic = 'force-dynamic';

const section = getAdminSection('feature-flags');

type FlagRow = {
  id: string;
  domain: string;
  route: string;
  capability: string;
  labelKey: string;
  method: string;
  endpoint: string;
  state: 'live' | 'unavailable';
};

const FLAGS: readonly FlagRow[] = DOMAIN_ROUTES.flatMap((route) =>
  route.capabilities.map((capability) => ({
    id: `${route.id}.${capability.id}`,
    domain: route.domain,
    route: route.pattern,
    capability: capability.id,
    labelKey: capability.labelKey,
    method: capability.method,
    endpoint: capability.endpoint ?? '',
    state: capability.endpoint !== null ? ('live' as const) : ('unavailable' as const),
  })),
);

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('platformOverview.title'),
    description: t('platformOverview.lead'),
    robots: { index: false, follow: false },
  };
}

export default async function FeatureFlagsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const query = await searchParams;
  setRequestLocale(locale);
  const t = await getTranslations();

  const wired = FLAGS.filter((row) => row.state === 'live').length;

  const columns: readonly AdminGridColumn<FlagRow>[] = [
    {
      id: 'capability',
      labelKey: 'statusPage.label',
      search: (row) => `${row.capability} ${row.labelKey} ${row.endpoint}`,
      compare: (a, b) => a.capability.localeCompare(b.capability),
      render: (row) => <span className="font-medium text-ink">{t(row.labelKey)}</span>,
    },
    {
      id: 'id',
      labelKey: 'market.template.method',
      search: (row) => row.id,
      compare: (a, b) => a.id.localeCompare(b.id),
      render: (row) => <span className="num text-xs text-ink-soft">{row.id}</span>,
    },
    {
      id: 'method',
      labelKey: 'market.template.method',
      search: (row) => row.method,
      compare: (a, b) => a.method.localeCompare(b.method),
      render: (row) => <span className="num text-xs">{row.method}</span>,
    },
    {
      id: 'endpoint',
      labelKey: 'statusPage.endpoint',
      search: (row) => row.endpoint,
      compare: (a, b) => a.endpoint.localeCompare(b.endpoint),
      render: (row) =>
        row.endpoint === '' ? (
          <StatusDot state="down" label={t('statusLine.unavailable')} />
        ) : (
          <span className="num break-all text-xs text-ink-soft">{row.endpoint}</span>
        ),
    },
  ];

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <div className="card mt-6 p-4">
        <dl className="grid gap-3 sm:grid-cols-2">
          <div>
            <dt className="field-label">{t('common.total')}</dt>
            <dd className="num mt-1 text-sm text-ink">
              {new Intl.NumberFormat(locale).format(FLAGS.length)}
            </dd>
          </div>
          <div>
            <dt className="field-label">{t('common.live')}</dt>
            <dd className="num mt-1 text-sm text-ink">
              {new Intl.NumberFormat(locale).format(wired)}
            </dd>
          </div>
        </dl>
        <p className="num mt-3 break-all text-xs text-ink-faint">{REGISTRY_FILE}</p>
      </div>

      <section className="mt-6" aria-labelledby="admin-flags-matrix">
        <h2 id="admin-flags-matrix" className="field-label">
          {t('market.template.contractTitle')}
        </h2>
        <div className="mt-3">
          <AdminDataGrid
            id="admin-flags-caption"
            caption={t('market.template.contractDescription')}
            source={REGISTRY_FILE}
            basePath={`/${locale}/admin/feature-flags`}
            searchParams={query}
            columns={columns}
            rows={FLAGS}
            rowId={(row) => row.id}
            emptyMessage={t('statusLine.noData')}
          />
        </div>
      </section>

      <section className="mt-6" aria-labelledby="admin-flags-settings">
        <h2 id="admin-flags-settings" className="field-label">
          {t('statusPage.state')}
        </h2>
        <div className="mt-3">
          <AdminUnavailable
            source="services/api_gateway/routers/admin_settings.py"
            detail={t('market.template.unavailableDescription')}
          />
        </div>
      </section>

      <AdminCapabilityTable id="admin-flags-contract" capabilities={section.capabilities} />

      <AdminSourceNote source={REGISTRY_FILE} ok />
    </div>
  );
}
