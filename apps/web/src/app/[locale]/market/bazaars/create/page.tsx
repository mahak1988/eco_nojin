import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { BazaarCreateForm } from '@/components/market/BazaarCreateForm';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { BAZAARS_SOURCE } from '@/lib/api/market';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.bazaarCreate');
  return {
    title: t('title'),
    description: t('lead'),
    robots: { index: false, follow: true },
  };
}

export default async function BazaarCreatePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.bazaarCreate');
  const statusPage = await getTranslations('statusPage');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-8">
        <header className="mb-8">
          <h1 className="display text-balance text-4xl font-bold text-ink">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
          <div className="mt-4">
            <ProvenanceStamp
              source={BAZAARS_SOURCE}
              label={statusPage('endpoint')}
              method={t('submit')}
            />
          </div>
        </header>
        <BazaarCreateForm />
      </div>
    </main>
  );
}
