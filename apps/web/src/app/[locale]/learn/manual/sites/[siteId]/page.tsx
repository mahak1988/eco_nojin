import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { SITE_URL as BASE_URL } from '@/config/site';
import {
  formatCell,
  getManualSite,
  manualClimateNormalsSource,
  manualSiteSource,
  manualSitesPathGuard,
  manualWeatherDailySource,
} from '@/lib/api/manual';

export const dynamic = 'force-dynamic';

const PATH = '/learn/manual/sites';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; siteId: string }>;
}): Promise<Metadata> {
  const { locale, siteId } = await params;
  const t = await getTranslations('manual.site');
  const path = `${PATH}/${siteId}`;
  return {
    title: t('title', { siteId }),
    description: t('description'),
    alternates: { canonical: `${BASE_URL}/${locale}${path}` },
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}${path}`,
      title: t('title', { siteId }),
    },
  };
}

export default async function ManualSitePage({
  params,
}: {
  params: Promise<{ locale: string; siteId: string }>;
}) {
  const { locale, siteId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('manual.site');
  const status = await getTranslations('statusLine');

  if (!manualSitesPathGuard(siteId)) notFound();
  const source = manualSiteSource(siteId);
  const result = await getManualSite(siteId);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <Link href={`/${locale}/learn/manual/sites`} className="text-sm text-water hover:underline">
          {t('back')}
        </Link>

        <section className="mt-6">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="display text-3xl font-bold text-ink">{t('title', { siteId })}</h1>
            <ProvenanceStamp source={source} verified={result.ok} method={source} />
          </div>
          <p className="mt-3 text-ink-soft">{t('description')}</p>
          <p className="num mt-2 break-all text-xs text-ink-faint">{source}</p>
        </section>

        <section className="mt-6">
          {result.ok ? (
            <>
              <Card density="compact">
                <dl className="grid gap-3 sm:grid-cols-2">
                  {Object.entries(result.data).map(([field, value]) => (
                    <div key={field}>
                      <dt className="num text-xs text-ink-soft">{field}</dt>
                      <dd className="mt-1 text-sm text-ink">{formatCell(value)}</dd>
                    </div>
                  ))}
                </dl>
              </Card>
              <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-ink-soft">
                <ProvenanceStamp source={source} verified method={source} />
                <span>{status('realData')}</span>
              </p>
            </>
          ) : (
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-sm font-medium text-ink">
                  {result.status === 0 ? t('offline') : status('unavailable')}
                </h2>
                <StatusDot
                  state={result.status === 0 ? 'down' : 'warn'}
                  label={status('unavailable')}
                />
              </div>
              <p className="num mt-2 text-sm text-ink-soft">
                {source} · {result.status || '—'} · {result.error}
              </p>
              <div className="mt-3">
                <ProvenanceStamp source={source} verified={false} method={source} />
              </div>
            </Card>
          )}
        </section>

        <section className="mt-8">
          <h2 className="text-sm font-medium text-ink">{t('related')}</h2>
          <ul className="mt-2 flex flex-col gap-2">
            <li>
              <Link
                href={`/${locale}/learn/manual/climate-normals/${siteId}`}
                className="text-sm text-water hover:underline"
              >
                {t('relatedNormals')}
              </Link>
              <span className="num ms-2 text-xs text-ink-faint">
                {manualClimateNormalsSource(siteId)}
              </span>
            </li>
            <li>
              <Link href={`/${locale}${PATH}`} className="text-sm text-water hover:underline">
                {t('back')}
              </Link>
              <span className="num ms-2 text-xs text-ink-faint">
                {manualWeatherDailySource(siteId)}
              </span>
            </li>
          </ul>
        </section>
      </div>
    </main>
  );
}
