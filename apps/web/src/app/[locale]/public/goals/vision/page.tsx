import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'چشم‌انداز', en: 'Vision' };
  const descriptions: Record<string, string> = { fa: 'چشم‌انداز ۱۰ ساله پلتفرم', en: '10-year platform vision' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/goals/vision`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/goals/vision`, languages: { fa: `${BASE_URL}/fa/public/goals/vision`, en: `${BASE_URL}/en/public/goals/vision` } },
  };
}

export default async function VisionPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.goals.vision');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Strategy Document" label={t('provenanceLabel')} verified={true} method="Strategic planning" timestamp="2024-12-01">
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
          evidence={['Backcasting from 2034', 'Stakeholder workshops', 'Scenario modeling']}
          limits={['Uncertainty increases with horizon', 'Policy environment volatile', 'Technology disruption risk']}
          next={['Annual vision review', 'Publish scenario updates', 'Link to investment plan']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('visionStatement')}</h2>
        <Card density="cozy">
          <div className="prose max-w-none text-ink">
            <p className="text-lg leading-relaxed">{t('statement')}</p>
          </div>
          <div className="mt-4">
            <ProvenanceStamp source="Strategy Document" verified={true} method="Strategic planning" timestamp="2024-12-01" label={t('provenanceLabel')} />
          </div>
        </Card>
      </section>
    </main>
  );
}