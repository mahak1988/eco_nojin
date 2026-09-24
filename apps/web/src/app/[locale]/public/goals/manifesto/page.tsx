import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'مانیفست', en: 'Manifesto' };
  const descriptions: Record<string, string> = { fa: 'مانیفست کامل پلتفرم', en: 'Full platform manifesto' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/goals/manifesto`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/goals/manifesto`, languages: { fa: `${BASE_URL}/fa/public/goals/manifesto`, en: `${BASE_URL}/en/public/goals/manifesto` } },
  };
}

export default async function ManifestoPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.goals.manifesto');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Manifesto Document" label={t('provenanceLabel')} verified={true} method="Community-signed" timestamp="2024-12-01">
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
          evidence={['Participatory drafting', 'Multi-language consensus', 'Digital signatures']}
          limits={['Living document', 'Translation sync challenges', 'Version control essential']}
          next={['Add annotation layer', 'Enable community proposals', 'Annual manifesto summit']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('manifestoText')}</h2>
        <Card density="cozy">
          <div className="prose max-w-none text-ink">
            <div className="space-y-4">
              <p>{t('para1')}</p>
              <p>{t('para2')}</p>
              <p>{t('para3')}</p>
              <p>{t('para4')}</p>
              <p>{t('para5')}</p>
            </div>
          </div>
          <div className="mt-4">
            <ProvenanceStamp source="Manifesto Document" verified={true} method="Community-signed" timestamp="2024-12-01" label={t('provenanceLabel')} />
          </div>
        </Card>
      </section>
    </main>
  );
}