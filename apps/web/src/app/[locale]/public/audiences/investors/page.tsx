import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Stat } from '@/components/ui/Stat';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'سرمایه‌گذاران', en: 'Investors' };
  const descriptions: Record<string, string> = { fa: 'فرصت‌های سرمایه‌گذاری در کربن، آب و کشاورزی تجدیدپذیر', en: 'Investment opportunities in carbon, water, regenerative agriculture' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/audiences/investors`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/audiences/investors`, languages: { fa: `${BASE_URL}/fa/public/audiences/investors`, en: `${BASE_URL}/en/public/audiences/investors` } },
  };
}

export default async function InvestorsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.audiences.investors');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Investment Memo" label={t('provenanceLabel')} verified={true} method="Financial modeling" timestamp="2024-12-01">
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
          evidence={['17 carbon projects', 'VVB-verified credits', 'Blended finance structures']}
          limits={['Market volatility', 'Policy risk', 'MRV cost curves']}
          next={['Launch green bond', 'Add portfolio tracker', 'Enable secondary market']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('opportunities')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card density="cozy">
            <h3 className="font-semibold text-ink mb-2">{t('opp1_title')}</h3>
            <p className="text-ink-soft mb-4">{t('opp1_desc')}</p>
            <Button variant="primary" size="sm">{t('learnMore')}</Button>
          </Card>
          <Card density="cozy">
            <h3 className="font-semibold text-ink mb-2">{t('opp2_title')}</h3>
            <p className="text-ink-soft mb-4">{t('opp2_desc')}</p>
            <Button variant="primary" size="sm">{t('learnMore')}</Button>
          </Card>
          <Card density="cozy">
            <h3 className="font-semibold text-ink mb-2">{t('opp3_title')}</h3>
            <p className="text-ink-soft mb-4">{t('opp3_desc')}</p>
            <Button variant="primary" size="sm">{t('learnMore')}</Button>
          </Card>
        </div>
      </section>
    </main>
  );
}