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
  const titles: Record<string, string> = { fa: 'جستجوی معنایی', en: 'Semantic Search' };
  const descriptions: Record<string, string> = { fa: 'جستجوی مبتنی بر معن و بردار', en: 'Vector-based semantic search' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/semantic`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/semantic`, languages: { fa: `${BASE_URL}/fa/market/search/semantic`, en: `${BASE_URL}/en/market/search/semantic` } },
  };
}

export default async function SemanticSearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.semantic');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Semantic Search Engine" label={t('provenanceLabel')} verified={true} method="Vector similarity" timestamp="2024-12-10">
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
          evidence={['pgvector embeddings', 'Multi-language models', 'Context-aware ranking']}
          limits={['Embedding quality varies', 'Computational cost', 'Beta feature']}
          next={['Add hybrid search', 'Enable filter combinations', 'Improve recall']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <div className="space-y-4">
            <div className="flex gap-3">
              <input type="text" placeholder={t('searchPlaceholder')} className="flex-1 px-4 py-3 rounded-lg border border-line bg-surface text-ink text-lg focus:outline-none focus:ring-2 focus:ring-forest" autoFocus />
              <Button variant="primary" size="lg" className="whitespace-nowrap">{common('search')}</Button>
            </div>
            <p className="text-sm text-ink-50">{t('hint')}</p>
          </div>
        </Card>
      </section>
    </main>
  );
}