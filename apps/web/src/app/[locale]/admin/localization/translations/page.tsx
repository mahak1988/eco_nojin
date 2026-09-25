import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminDataGrid, type AdminGridColumn } from '@/components/admin/AdminDataGrid';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import {
  AdminCapabilityTable,
  AdminSourceNote,
  AdminUnavailable,
} from '@/components/admin/AdminStates';
import {
  type AdminLocaleRow,
  MESSAGES_GLOB_PATH,
  readLocaleCoverage,
} from '@/components/admin/admin-local-data';
import { getAdminSection } from '@/components/admin/admin-sections';
import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';

// Coverage is read from the catalogues on disk on every request.
export const dynamic = 'force-dynamic';

const section = getAdminSection('localization');
const MESSAGES_SOURCE = MESSAGES_GLOB_PATH;

type LocaleRow = AdminLocaleRow & { machineLabel: string };

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('auth.session.language'),
    description: t('statusPage.subtitle'),
    robots: { index: false, follow: false },
  };
}

export default async function LocalizationPage({
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

  const session = await readAdminSession();
  const token = adminToken(session);
  const [coverage, legalLocales] = await Promise.all([
    readLocaleCoverage(),
    adminGet<string[]>(token, '/api/v1/legal-texts/locales'),
  ]);

  const rows: LocaleRow[] = coverage.ok
    ? coverage.data.map((row) => ({
        ...row,
        machineLabel: row.machineTranslated ? t('common.demo') : t('common.live'),
      }))
    : [];

  const numberFormat = new Intl.NumberFormat(locale);
  const columns: readonly AdminGridColumn<LocaleRow>[] = [
    {
      id: 'locale',
      labelKey: 'auth.session.language',
      search: (row) => row.locale,
      compare: (a, b) => a.locale.localeCompare(b.locale),
      render: (row) => (
        <span className="block">
          <span className="num block font-medium text-ink">{row.locale}</span>
          <span className="block text-[0.65rem] text-ink-soft">{row.machineLabel}</span>
        </span>
      ),
    },
    {
      id: 'own',
      labelKey: 'statusPage.label',
      numeric: true,
      search: (row) => String(row.ownKeys),
      compare: (a, b) => a.ownKeys - b.ownKeys,
      render: (row) => <span className="num">{numberFormat.format(row.ownKeys)}</span>,
    },
    {
      id: 'effective',
      labelKey: 'common.total',
      numeric: true,
      search: (row) => String(row.effectiveKeys),
      compare: (a, b) => a.effectiveKeys - b.effectiveKeys,
      render: (row) => <span className="num">{numberFormat.format(row.effectiveKeys)}</span>,
    },
    {
      id: 'missing',
      labelKey: 'common.limits',
      numeric: true,
      search: (row) => String(row.missingKeys),
      compare: (a, b) => a.missingKeys - b.missingKeys,
      render: (row) => (
        <span className={`num ${row.missingKeys === 0 ? '' : 'text-copper'}`}>
          {numberFormat.format(row.missingKeys)}
        </span>
      ),
    },
  ];

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <section className="mt-6" aria-labelledby="admin-locale-coverage">
        <h2 id="admin-locale-coverage" className="field-label">
          {t('common.total')}
        </h2>
        <div className="mt-3">
          {coverage.ok ? (
            <AdminDataGrid
              id="admin-locale-caption"
              caption={t('statusPage.subtitle')}
              source={MESSAGES_SOURCE}
              basePath={`/${locale}/admin/localization/translations`}
              searchParams={query}
              columns={columns}
              rows={rows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <AdminUnavailable
              source={MESSAGES_SOURCE}
              status={coverage.status}
              detail={coverage.error}
            />
          )}
        </div>
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="card p-5">
          <h2 className="field-label">{t('common.machineTranslatedNotice')}</h2>
          <p className="num mt-2 text-sm text-ink">
            {coverage.ok
              ? `${coverage.data.filter((row) => row.machineTranslated).length} / ${
                  coverage.data.length
                }`
              : t('statusLine.unavailable')}
          </p>
        </div>
        <div className="card p-5">
          <h2 className="field-label">{t('legal.title')}</h2>
          <p className="num mt-2 text-sm text-ink">
            {legalLocales.ok ? legalLocales.data.join(' · ') : t('statusLine.unavailable')}
          </p>
          <p className="num mt-2 text-xs text-ink-faint">/api/v1/legal-texts/locales</p>
        </div>
      </section>

      <AdminCapabilityTable id="admin-locale-contract" capabilities={section.capabilities} />

      <AdminSourceNote
        source={`${MESSAGES_SOURCE} · /api/v1/legal-texts/locales`}
        ok={coverage.ok && legalLocales.ok}
      />
    </div>
  );
}
