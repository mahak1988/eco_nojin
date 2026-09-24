import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'پیشنهادهای زنده', en: 'Live Suggestions' };
  const descriptions: Record<string, string> = { fa: 'پیشنهادات جستجوی بلادرنگ', en: 'Real-time search suggestions' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/suggestions`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/suggestions`, languages: { fa: `${BASE_URL}/fa/market/search/suggestions`, en: `${BASE_URL}/en/market/search/suggestions` } },
  };
}

export default async function SuggestionsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.suggestions');
  const common = await getTranslations('common');

  const mockSuggestions = ['پسته ارگانیک', 'زعفران سوپر نگین', 'بادام ممان', 'خرما مضافتی', 'عسل طبیعی', 'رب انار'];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Suggestion Engine" label={t('provenanceLabel')} verified={true} method="Prefix + popularity" timestamp="2024-12-10">
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
          evidence={['Prefix matching', 'Popularity ranking', 'Multi-language']}
          limits={['Latency < 50ms', 'Cache freshness', 'Personalization WIP']}
          next={['Add semantic suggestions', 'Enable personalization', 'Voice prefix']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <p className="text-ink-soft mb-4">{t('popularSearches')}</p>
          <div className="flex flex-wrap gap-2">
            {mockSuggestions.map(s => (
              <button key={s} className="px-3 py-1.5 rounded border border-line bg-surface text-ink-soft hover:bg-forest/5 text-sm" onClick={() => {}}>
                {s}
              </button>
            ))}
          </div>
        </Card>
      </section>
    </main>
  );
}