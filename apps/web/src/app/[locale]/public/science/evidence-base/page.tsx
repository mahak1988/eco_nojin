import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Stat } from '@/components/ui/Stat';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface EvidenceItem {
  id: string;
  title: string;
  doi: string;
  source: string;
  verified: boolean;
  method: string;
  timestamp: string;
}

const MOCK_EVIDENCE: EvidenceItem[] = [
  { id: 'e1', title: 'Soil Carbon Sequestration in Semi-Arid Regions', doi: '10.1016/j.geoderma.2024.116789', source: 'Geoderma Journal', verified: true, method: 'Peer-reviewed meta-analysis', timestamp: '2024-03-15' },
  { id: 'e2', title: 'FAO-56 Evapotranspiration Validation', doi: '10.1016/j.agwat.2023.108234', source: 'Agricultural Water Management', verified: true, method: 'Multi-site field trials', timestamp: '2023-11-20' },
  { id: 'e3', title: 'RUSLE Erosion Modeling for Iranian Watersheds', doi: '10.1016/j.catena.2024.107891', source: 'CATENA', verified: true, method: 'Calibrated with 127 plots', timestamp: '2024-01-10' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'پایه‌های علمی', en: 'Scientific Evidence Base' };
  const descriptions: Record<string, string> = { fa: 'مجموعه شواهد علمی با DOI و وضعیت تأیید', en: 'Curated scientific evidence with DOI and verification status' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/evidence-base`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/evidence-base`, languages: { fa: `${BASE_URL}/fa/public/science/evidence-base`, en: `${BASE_URL}/en/public/science/evidence-base` } },
  };
}

export default async function EvidenceBasePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.evidenceBase');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Evidence Registry" label={t('provenanceLabel')} verified={true} method="DOI-indexed" timestamp="2024-12-01">
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
          evidence={['FAO/IPCC/OGC standards', 'Peer-reviewed DOIs', 'Reproducible pipelines']}
          limits={['Modelled estimates flagged', 'Regional calibration gaps', 'Translation pending for 12 locales']}
          next={['Add living systematic reviews', 'Link to model registry', 'Enable evidence gap maps']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('evidenceCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_EVIDENCE.map(item => (
            <Card key={item.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{item.title}</h3>
                  <p className="text-sm text-ink-soft">DOI: <code className="font-mono">{item.doi}</code></p>
                </div>
                <ProvenanceStamp source={item.source} verified={item.verified} method={item.method} timestamp={item.timestamp} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}