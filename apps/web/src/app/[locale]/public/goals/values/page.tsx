import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'ارزش‌ها', en: 'Values' };
  const descriptions: Record<string, string> = { fa: 'ارزش‌های بنیادین پلتفرم', en: 'Core platform values' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/goals/values`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/goals/values`, languages: { fa: `${BASE_URL}/fa/public/goals/values`, en: `${BASE_URL}/en/public/goals/values` } },
  };
}

export default async function ValuesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.goals.values');
  const common = await getTranslations('common');

  const values = [
    { title: t('v1_title'), desc: t('v1_desc') },
    { title: t('v2_title'), desc: t('v2_desc') },
    { title: t('v3_title'), desc: t('v3_desc') },
    { title: t('v4_title'), desc: t('v4_desc') },
    { title: t('v5_title'), desc: t('v5_desc') },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Culture Charter" label={t('provenanceLabel')} verified={true} method="Team-defined" timestamp="2024-12-01">
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
          evidence={['Co-created with team', 'Aligned with mission', 'Behavioral indicators defined']}
          limits={['Cultural interpretation varies', 'Enforcement mechanisms soft', 'Annual reassessment needed']}
          next={['Embed in hiring', 'Add to performance reviews', 'Publish culture deck']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('valuesList')}</h2>
        <div className="grid gap-4">
          {values.map((v, i) => (
            <Card key={i} density="compact">
              <h3 className="font-medium text-ink">{v.title}</h3>
              <p className="text-sm text-ink-soft mt-1">{v.desc}</p>
            </Card>
          ))}
        </div>
        <div className="mt-6">
            <ProvenanceStamp source="Culture Charter" verified={true} method="Team-defined" timestamp="2024-12-01" label={t('provenanceLabel')} />
          </div>
      </section>
    </main>
  );
}