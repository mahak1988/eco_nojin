import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'جستجوی تصویر', en: 'Image Search' };
  const descriptions: Record<string, string> = { fa: 'جستجوی محصول با آپلود تصویر', en: 'Product search by image upload' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/image`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/image`, languages: { fa: `${BASE_URL}/fa/market/search/image`, en: `${BASE_URL}/en/market/search/image` } },
  };
}

export default async function ImageSearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.image');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Image Search Engine" label={t('provenanceLabel')} verified={true} method="CNN similarity" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['CNN similarity', 'Multi-category', 'Real-time results']}
          limits={['Accuracy varies', 'Lighting dependent', 'Beta']}
          next={['Add disease detection', 'Improve accuracy', 'Offline model']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <div className="aspect-video flex items-center justify-center bg-slate/10 rounded border-2 border-dashed border-line mb-4">
            <div className="text-center">
              <span className="text-6xl">📷</span>
              <p className="mt-2 text-ink-soft">{t('dropImage')}</p>
              <p className="text-xs text-ink-soft">{t('formatHint')}</p>
            </div>
          </div>
          <Button variant="primary" className="w-full">{t('uploadImage')}</Button>
          <p className="mt-2 text-center text-xs text-ink-soft">{t('orCamera')}</p>
          <Button variant="secondary" className="w-full mt-2">{t('useCamera')}</Button>
        </Card>
      </section>
    </main>
  );
}