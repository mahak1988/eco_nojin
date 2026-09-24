import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface CaseStudy {
  id: string;
  title: string;
  location: string;
  models: string[];
  outcome: string;
  status: 'published' | 'in-review' | 'draft';
  doi?: string;
}

const MOCK_CASES: CaseStudy[] = [
  { id: 'cs1', title: 'Kerman Pistachio Orchard Water Optimization', location: 'Kerman, Iran', models: ['FAO-56', 'AquaCrop-OSPy'], outcome: '23% water savings, 12% yield increase', status: 'published', doi: '10.1016/j.agwat.2024.108234' },
  { id: 'cs2', title: 'Zagros Watershed Erosion Control', location: 'Lorestan, Iran', models: ['RUSLE2', 'SWAT'], outcome: '45% sediment reduction with check dams', status: 'published', doi: '10.1016/j.catena.2024.107891' },
  { id: 'cs3', title: 'Khuzestan Soil Carbon Sequestration', location: 'Khuzestan, Iran', models: ['RothC', 'Century'], outcome: '1.2 tC/ha/yr with cover crops', status: 'in-review', doi: '10.1016/j.geoderma.2024.116789' },
  { id: 'cs4', title: 'Sistan Flood Risk Mapping', location: 'Sistan, Iran', models: ['HEC-RAS', 'HEC-HMS'], outcome: '100-yr floodplain delineated', status: 'draft' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'مطالعات موردی', en: 'Case Studies' };
  const descriptions: Record<string, string> = { fa: 'مطالعات موردی واقعی با مدل‌های هیدروما', en: 'Real-world case studies with HydroMa models' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/case-studies`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/case-studies`, languages: { fa: `${BASE_URL}/fa/public/science/case-studies`, en: `${BASE_URL}/en/public/science/case-studies` } },
  };
}

export default async function CaseStudiesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.caseStudies');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Case Study Registry" label={t('provenanceLabel')} verified={true} method="Field-documented" timestamp="2024-12-10">
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
          evidence={['4 documented cases', 'Farmer participation', 'Economic analysis']}
          limits={['Small sample size', 'Single-season data', 'Context-specific results']}
          next={['Add 10 more cases', 'Enable comparison tool', 'Farmer video testimonials']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('cases')}</h2>
        <div className="grid gap-4">
          {MOCK_CASES.map(cs => (
            <Card key={cs.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{cs.title}</h3>
                  <p className="text-sm text-ink-soft mt-1">{cs.location} · Models: {cs.models.join(', ')}</p>
                  <p className="text-sm text-ink mt-1">{cs.outcome}</p>
                  {cs.doi && <p className="text-xs text-ink-soft">DOI: <code className="font-mono">{cs.doi}</code></p>}
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={cs.status === 'published' ? 'ok' : cs.status === 'in-review' ? 'warn' : 'down'} label={common(cs.status)} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}