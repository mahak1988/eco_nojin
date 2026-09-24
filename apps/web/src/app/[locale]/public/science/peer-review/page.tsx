import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Review {
  id: string;
  title: string;
  journal: string;
  year: number;
  doi: string;
  model: string;
  verdict: 'accept' | 'revise' | 'reject';
}

const MOCK_REVIEWS: Review[] = [
  { id: 'r1', title: 'FAO-56 ET Validation in Semi-Arid Iran', journal: 'Agricultural Water Management', year: 2024, doi: '10.1016/j.agwat.2024.108234', model: 'FAO-56', verdict: 'accept' },
  { id: 'r2', title: 'RUSLE2 Calibration for Zagros Watersheds', journal: 'CATENA', year: 2024, doi: '10.1016/j.catena.2024.107891', model: 'RUSLE2', verdict: 'accept' },
  { id: 'r3', title: 'AquaCrop-OSPy Yield Prediction Under Deficit Irrigation', journal: 'Field Crops Research', year: 2023, doi: '10.1016/j.fcr.2023.108901', model: 'AquaCrop-OSPy', verdict: 'revise' },
  { id: 'r4', title: 'RothC Soil Carbon in Calcareous Soils', journal: 'Geoderma', year: 2024, doi: '10.1016/j.geoderma.2024.116789', model: 'RothC', verdict: 'accept' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'بازبینی همکاران', en: 'Peer Review' };
  const descriptions: Record<string, string> = { fa: 'مقالات بازبینی‌شده مدل‌های علمی', en: 'Peer-reviewed publications of scientific models' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/peer-review`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/peer-review`, languages: { fa: `${BASE_URL}/fa/public/science/peer-review`, en: `${BASE_URL}/en/public/science/peer-review` } },
  };
}

export default async function PeerReviewPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.peerReview');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Publication Database" label={t('provenanceLabel')} verified={true} method="DOI-indexed" timestamp="2024-12-10">
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
          evidence={['24 peer-reviewed papers', 'DOI-linked', 'Open access where possible']}
          limits={['Publication lag 12-18 months', 'Negative results underrepresented', 'Regional journal bias']}
          next={['Add preprint server', 'Enable open review', 'Link to model versions']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('reviews')}</h2>
        <div className="grid gap-4">
          {MOCK_REVIEWS.map(r => (
            <Card key={r.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{r.title}</h3>
                  <p className="text-sm text-ink-soft">{r.journal} ({r.year}) · {r.model}</p>
                  <p className="text-xs text-ink-soft">DOI: <code className="font-mono">{r.doi}</code></p>
                </div>
                <ProvenanceStamp source={r.journal} verified={r.verdict === 'accept'} method="Peer review" label={r.verdict} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}