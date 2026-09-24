import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface ProfilerFeature {
  id: string;
  name: string;
  description: string;
  status: 'live' | 'beta' | 'planned';
  apiEndpoint: string;
  source: string;
}

const MOCK_FEATURES: ProfilerFeature[] = [
  { id: 'pf1', name: 'Polygon Editor', description: 'Draw/edit land boundaries on map', status: 'live', apiEndpoint: 'POST /api/land/polygons', source: 'land service' },
  { id: 'pf2', name: 'Soil Profile', description: 'Depth-based soil properties from SoilGrids', status: 'live', apiEndpoint: 'GET /api/land/soil-profile', source: 'satellite service' },
  { id: 'pf3', name: 'Climate Normals', description: '30-year climate averages (ERA5)', status: 'live', apiEndpoint: 'GET /api/land/climate', source: 'climate service' },
  { id: 'pf4', name: 'Hydrology Indices', description: 'FAO-56 ET, runoff, infiltration', status: 'beta', apiEndpoint: 'POST /api/land/hydrology', source: 'hydrology service' },
  { id: 'pf5', name: 'Carbon Potential', description: 'Sequestration scenarios (RothC)', status: 'planned', apiEndpoint: 'POST /api/land/carbon', source: 'carbon service' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'نمایشگاه پروفایلر زمین', en: 'Land Profiler Demo' };
  const descriptions: Record<string, string> = { fa: 'تحلیل زمین و سناریوهای مدیریتی', en: 'Land analysis and management scenarios' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/components/land-profiler`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/components/land-profiler`, languages: { fa: `${BASE_URL}/fa/public/components/land-profiler`, en: `${BASE_URL}/en/public/components/land-profiler` } },
  };
}

export default async function LandProfilerPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.components.landProfiler');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Land Registry" label={t('provenanceLabel')} verified={true} method="Multi-source" timestamp="2024-12-10">
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
          evidence={['Polygon-based analysis', 'Multi-layer data fusion', 'Scenario comparison']}
          limits={['Carbon scenarios WIP', 'Economic valuation missing', 'Offline mode limited']}
          next={['Add economic module', 'Enable PDF reports', 'Offline WASM bundle']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('features')}</h2>
        <div className="grid gap-4">
          {MOCK_FEATURES.map(f => (
            <Card key={f.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{f.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {f.status === 'live' ? 'bg-forest/10 text-forest' :
                       f.status === 'beta' ? 'bg-amber/10 text-amber' :
                       'bg-slate/10 text-slate'}">
                      {f.status}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{f.description}</p>
                  <p className="text-xs text-ink-soft font-mono">{f.apiEndpoint}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={f.status === 'live' ? 'ok' : f.status === 'beta' ? 'warn' : 'down'} label={common(f.status)} />
                  <ProvenanceStamp source={f.source} verified={true} method="OpenAPI" label={f.status} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}