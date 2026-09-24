import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'چرا اکو نوژین', en: 'Why Eco Nojin' };
  const descriptions: Record<string, string> = { fa: 'مسئله و پاسخ: چرا این پلتفرم؟', en: 'Problem→Solution: Why this platform?' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/why`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/why`, languages: { fa: `${BASE_URL}/fa/public/why`, en: `${BASE_URL}/en/public/why` } },
  };
}

export default async function WhyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.why');
  const common = await getTranslations('common');

  const problems = [
    { problem: t('p1_problem'), solution: t('p1_solution') },
    { problem: t('p2_problem'), solution: t('p2_solution') },
    { problem: t('p3_problem'), solution: t('p3_solution') },
    { problem: t('p4_problem'), solution: t('p4_solution') },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Platform Strategy" label={t('provenanceLabel')} verified={true} method="Stakeholder workshops" timestamp="2024-12-01">
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
          evidence={['Field research 2023-24', 'Stakeholder interviews', 'Pilot validation']}
          limits={['Regional generalization limited', 'Long-term impact TBC', 'Cost-benefit per context varies']}
          next={['Publish impact report', 'Expand to 3 countries', 'Add economic valuation']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('problemSolutionTable')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('problem')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('solution')}</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((p, i) => (
                <tr key={i} className="border-b border-line/50">
                  <td className="py-2 px-3 text-ink-soft">{p.problem}</td>
                  <td className="py-2 px-3 text-ink">{p.solution}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6">
        <ProvenanceStamp source="Platform Strategy" verified={true} method="Workshops" timestamp="2024-12-01" label={t('provenanceLabel')} />
      </div>
      </section>
    </main>
  );
}