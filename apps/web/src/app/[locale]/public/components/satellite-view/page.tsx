import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface SatelliteLayer {
  id: string;
  name: string;
  source: string;
  resolution: string;
  revisit: string;
  status: 'active' | 'degraded' | 'planned';
  bands: string[];
}

const MOCK_LAYERS: SatelliteLayer[] = [
  { id: 'sl1', name: 'Sentinel-2 L2A', source: 'Copernicus', resolution: '10m', revisit: '5 days', status: 'active', bands: ['B2','B3','B4','B8','B11','B12'] },
  { id: 'sl2', name: 'Landsat 8/9', source: 'USGS/NASA', resolution: '30m', revisit: '16 days', status: 'active', bands: ['B2','B3','B4','B5','B6','B7'] },
  { id: 'sl3', name: 'Sentinel-1 SAR', source: 'Copernicus', resolution: '10m', revisit: '6 days', status: 'active', bands: ['VV','VH'] },
  { id: 'sl4', name: 'PlanetScope', source: 'Planet Labs', resolution: '3m', revisit: 'Daily', status: 'planned', bands: ['B1','B2','B3','B4'] },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'نمایشگاه ماهواره', en: 'Satellite View Demo' };
  const descriptions: Record<string, string> = { fa: 'لایه‌های داده ماهواره‌ای و ویژوالایزیشن', en: 'Satellite data layers and visualization' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/components/satellite-view`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/components/satellite-view`, languages: { fa: `${BASE_URL}/fa/public/components/satellite-view`, en: `${BASE_URL}/en/public/components/satellite-view` } },
  };
}

export default async function SatelliteViewPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.components.satelliteView');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Satellite Catalog" label={t('provenanceLabel')} verified={true} method="STAC-indexed" timestamp="2024-12-10">
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
          evidence={['Multi-sensor fusion', 'STAC catalog integration', 'Cloud-optimized COGs']}
          limits={['Cloud masking gaps', 'Atmospheric correction WIP', 'Real-time streaming not live']}
          next={['Add Sentinel-3 OLCI', 'Enable on-the-fly indices', 'Integrate with MapLibre']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('layers')}</h2>
        <div className="grid gap-4">
          {MOCK_LAYERS.map(l => (
            <Card key={l.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{l.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {l.status === 'active' ? 'bg-forest/10 text-forest' :
                       l.status === 'degraded' ? 'bg-amber/10 text-amber' :
                       'bg-slate/10 text-slate'}">
                      {l.status}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{l.source} · {l.resolution} · Revisit: {l.revisit}</p>
                  <p className="text-xs text-ink-soft">Bands: {l.bands.join(', ')}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={l.status === 'active' ? 'ok' : l.status === 'degraded' ? 'warn' : 'down'} label={common(l.status)} />
                  <ProvenanceStamp source="STAC Catalog" verified={true} method="OpenAPI" label={l.status} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}