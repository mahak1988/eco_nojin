import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ManualDatasetPage } from '@/components/manual/ManualDatasetPage';
import { SITE_URL as BASE_URL } from '@/config/site';
import {
  getManualClimateNormals,
  manualClimateNormalsSource,
  manualSitesPathGuard,
} from '@/lib/api/manual';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; siteId: string }>;
}): Promise<Metadata> {
  const { locale, siteId } = await params;
  const t = await getTranslations('manual.normals');
  const path = `/learn/manual/climate-normals/${siteId}`;
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

export default async function ClimateNormalsPage({
  params,
}: {
  params: Promise<{ locale: string; siteId: string }>;
}) {
  const { locale, siteId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('manual.normals');

  if (!manualSitesPathGuard(siteId)) notFound();

  return (
    <ManualDatasetPage
      locale={locale}
      source={manualClimateNormalsSource(siteId)}
      title={t('title', { siteId })}
      description={t('description')}
      emptyTitle={t('emptyTitle')}
      emptyDescription={t('emptyDescription')}
      result={await getManualClimateNormals(siteId)}
      rowsKey="months"
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
