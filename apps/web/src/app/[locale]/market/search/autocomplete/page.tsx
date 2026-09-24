import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'اتکمیل خودکار', en: 'Autocomplete' };
  const descriptions: Record<string, string> = { fa: 'اتکمیل پرس‌وجو برای تجربه سریع‌تر', en: 'Query autocomplete for faster search' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/autocomplete`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/autocomplete`, languages: { fa: `${BASE_URL}/fa/market/search/autocomplete`, en: `${BASE_URL}/en/market/search/autocomplete` } },
  };
}

export default async function AutocompletePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.autocomplete');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Autocomplete Engine" label={t('provenanceLabel')} verified={true} method="Trie + prefix" timestamp="2024-12-10">
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
          evidence={['Trie-based prefix', 'Sub-10ms latency', 'Fuzzy matching']}
          limits={['Memory usage', 'Index rebuild time', 'Multi-script support']}
          next={['Add suffix autocomplete', 'Enable phrase completion', 'Personalized ranking']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <p className="text-ink-soft mb-4">{t('demoPlaceholder')}</p>
          <input type="text" placeholder={t('typeToSee')} className="w-full px-4 py-3 rounded-lg border border-line bg-surface text-ink text-lg focus:outline-none focus:ring-2 focus:ring-forest" />
        </Card>
      </section>
    </main>
  );
}