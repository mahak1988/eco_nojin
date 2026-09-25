import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'چرا اکو نوژین', en: 'Why Eco Nojin' };
  const descriptions: Record<string, string> = {
    fa: 'مسئله و پاسخ: چرا این پلتفرم؟',
    en: 'Problem→Solution: Why this platform?',
  };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/why`,
      title: titles[locale] ?? titles.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/why`,
      languages: { fa: `${BASE_URL}/fa/public/why`, en: `${BASE_URL}/en/public/why` },
    },
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
        <ProvenanceStamp
          source={t('provenanceLabel')}
          label={t('provenanceLabel')}
          verified={false}
          method={t('provenanceLabel')}
        >
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
          evidence={t.raw('evidenceItems') as string[]}
          limits={t.raw('limitsItems') as string[]}
          next={t.raw('nextItems') as string[]}
          evidenceLabel={common('evidence')}
          limitsLabel={common('limits')}
          nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('problemSolutionTable')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-start py-2 px-3 font-medium text-ink-soft">{t('problem')}</th>
                <th className="text-start py-2 px-3 font-medium text-ink-soft">{t('solution')}</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((p) => (
                <tr key={p.problem} className="border-b border-line/50">
                  <td className="py-2 px-3 text-ink-soft">{p.problem}</td>
                  <td className="py-2 px-3 text-ink">{p.solution}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6">
          <ProvenanceStamp
            source={t('provenanceLabel')}
            verified={false}
            method={t('provenanceLabel')}
            label={t('provenanceLabel')}
          />
        </div>
      </section>
    </main>
  );
}
