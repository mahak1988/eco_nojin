import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'مکتش', en: 'Mission' };
  const descriptions: Record<string, string> = { fa: 'بیانیه‌مکتش پلتفرم', en: 'Platform mission statement' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/goals/mission`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/goals/mission`, languages: { fa: `${BASE_URL}/fa/public/goals/mission`, en: `${BASE_URL}/en/public/goals/mission` } },
  };
}

export default async function MissionPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.goals.mission');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Governance Charter" label={t('provenanceLabel')} verified={true} method="Board-approved" timestamp="2024-12-01">
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
          evidence={['Stakeholder consensus', 'Aligned with SDGs', 'Board ratified']}
          limits={['Aspirational language', 'Measurable targets in roadmap', 'Annual review cycle']}
          next={['Publish KPI dashboard', 'Annual mission audit', 'Community feedback loop']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('missionStatement')}</h2>
        <Card density="cozy">
          <div className="prose max-w-none text-ink">
            <p className="text-lg leading-relaxed">{t('statement')}</p>
          </div>
          <div className="mt-4">
            <ProvenanceStamp source="Governance Charter" verified={true} method="Board-approved" timestamp="2024-12-01" label={t('provenanceLabel')} />
          </div>
        </Card>
      </section>
    </main>
  );
}