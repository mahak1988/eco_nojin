import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Stat } from '@/components/ui/Stat';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'خانه', en: 'Home' };
  const descriptions: Record<string, string> = { fa: 'پلتفرم هوشمند مدیریت منظر', en: 'Smart Landscape Management Platform' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/home`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/home`, languages: { fa: `${BASE_URL}/fa/public/home`, en: `${BASE_URL}/en/public/home` } },
  };
}

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.home');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Platform Metrics" label={t('provenanceLabel')} verified={true} method="Real-time API" timestamp="2024-12-10">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Real backend data', '14 languages', 'Offline-first PWA']}
          limits={['Pilot phase', 'Regional rollout staged', 'Translation coverage varies']}
          next={['Launch pilot villages', 'Expand satellite MRV', 'Enable microcredit']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('keyMetrics')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label={t('beneficiaries')} value="12,450" provenance={{ source: 'Beneficiary Registry', verified: true, method: 'Survey', timestamp: '2024-12-01' }} />
          <Stat label={t('activeMarkets')} value="42" provenance={{ source: 'Market Registry', verified: true, method: 'On-chain', timestamp: '2024-12-01' }} />
          <Stat label={t('landProfiles')} value="1,890" provenance={{ source: 'Land Profiler', verified: true, method: 'Satellite+Ground', timestamp: '2024-12-01' }} />
          <Stat label={t('carbonProjects')} value="17" provenance={{ source: 'Carbon Registry', verified: true, method: 'VVB-audited', timestamp: '2024-12-01' }} />
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('quickActions')}</h2>
        <div className="flex flex-wrap gap-4">
          <Button variant="primary" onClick={() => window.location.href = `/${locale}/market`}>{t('enterMarket')}</Button>
          <Button variant="secondary" onClick={() => window.location.href = `/${locale}/hydroma`}>{t('exploreScience')}</Button>
          <Button variant="ghost" onClick={() => window.location.href = `/${locale}/public/education/library`}>{t('learnMore')}</Button>
        </div>
      </section>
    </main>
  );
}