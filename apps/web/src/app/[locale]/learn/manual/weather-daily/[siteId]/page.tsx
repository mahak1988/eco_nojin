import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ManualDatasetPage } from '@/components/manual/ManualDatasetPage';
import { SITE_URL as BASE_URL } from '@/config/site';
import {
  getManualWeatherDaily,
  manualSitesPathGuard,
  manualWeatherDailySource,
} from '@/lib/api/manual';

export const dynamic = 'force-dynamic';

/** The gateway caps one response at 1000 rows; 200 keeps the page readable. */
const ROW_LIMIT = 200;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; siteId: string }>;
}): Promise<Metadata> {
  const { locale, siteId } = await params;
  const t = await getTranslations('manual.weather');
  const path = `/learn/manual/weather-daily/${siteId}`;
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

export default async function WeatherDailyPage({
  params,
}: {
  params: Promise<{ locale: string; siteId: string }>;
}) {
  const { locale, siteId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('manual.weather');

  if (!manualSitesPathGuard(siteId)) notFound();

  return (
    <ManualDatasetPage
      locale={locale}
      source={`${manualWeatherDailySource(siteId)}?limit=${ROW_LIMIT}`}
      title={t('title', { siteId })}
      description={t('description')}
      emptyTitle={t('emptyTitle')}
      emptyDescription={t('emptyDescription')}
      result={await getManualWeatherDaily(siteId, ROW_LIMIT)}
      rowsKey="rows"
    >
      <p className="mt-6 text-sm">
        <Link
          href={`/${locale}/learn/manual/sites/${siteId}`}
          className="text-water hover:underline"
        >
          {t('backToSite')}
        </Link>
      </p>
    </ManualDatasetPage>
  );
}
