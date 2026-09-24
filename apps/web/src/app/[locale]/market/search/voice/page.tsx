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
  const titles: Record<string, string> = { fa: 'جستجوی صوتی', en: 'Voice Search' };
  const descriptions: Record<string, string> = { fa: 'جستجوی محصول با دستور صوتی', en: 'Product search by voice command' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/voice`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/voice`, languages: { fa: `${BASE_URL}/fa/market/search/voice`, en: `${BASE_URL}/en/market/search/voice` } },
  };
}

export default async function VoiceSearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.voice');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Voice Search Engine" label={t('provenanceLabel')} verified={true} method="ASR + NLP" timestamp="2024-12-10">
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
          evidence={['14 language ASR', 'Intent classification', 'Offline model']}
          limits={['Accuracy varies by accent', 'Background noise', 'Beta feature']}
          next={['Improve dialect support', 'Add voice commands', 'Offline model']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <div className="aspect-square flex flex-col items-center justify-center bg-slate/10 rounded border-2 border-dashed border-line mb-4">
            <span className="text-6xl">🎤</span>
            <p className="mt-2 text-ink-soft">{t('tapToSpeak')}</p>
            <p className="text-xs text-ink-soft">{t('listeningHint')}</p>
          </div>
          <Button variant="primary" className="w-full">{t('startListening')}</Button>
        </Card>
      </section>
    </main>
  );
}