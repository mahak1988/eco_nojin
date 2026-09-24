import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface SatelliteProduct {
  id: string;
  name: string;
  provider: string;
  resolution: string;
  revisit: string;
  bands: string[];
  status: 'live' | 'beta' | 'planned';
  apiEndpoint: string;
  source: string;
}

const MOCK_PRODUCTS: SatelliteProduct[] = [
  { id: 'sp1', name: 'Sentinel-2 L2A NDVI', provider: 'Copernicus', resolution: '10m', revisit: '5 days', bands: ['B2','B3','B4','B8'], status: 'live', apiEndpoint: 'GET /api/satellite/sentinel2/ndvi', source: 'satellite service' },
  { id: 'sp2', name: 'Sentinel-1 SAR Backscatter', provider: 'Copernicus', resolution: '10m', revisit: '6 days', bands: ['VV','VH'], status: 'live', apiEndpoint: 'GET /api/satellite/sentinel1/backscatter', source: 'satellite service' },
  { id: 'sp3', name: 'Landsat 8/9 Surface Reflectance', provider: 'USGS/NASA', resolution: '30m', revisit: '16 days', bands: ['B2','B3','B4','B5','B6','B7'], status: 'live', apiEndpoint: 'GET /api/satellite/landsat/sr', source: 'satellite service' },
  { id: 'sp4', name: 'PlanetScope Daily Mosaic', provider: 'Planet Labs', resolution: '3m', revisit: 'Daily', bands: ['B1','B2','B3','B4'], status: 'beta', apiEndpoint: 'GET /api/satellite/planet/daily', source: 'satellite service' },
  { id: 'sp5', name: 'Sentinel-3 OLCI Chlorophyll', provider: 'Copernicus', resolution: '300m', revisit: '2 days', bands: ['OC1','OC2'], status: 'planned', apiEndpoint: 'GET /api/satellite/sentinel3/chlorophyll', source: 'satellite service' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'استخبارات ماهواره‌ای', en: 'Satellite Intelligence' };
  const descriptions: Record<string, string> = { fa: 'محصولات و اندپوینت‌های داده ماهواره', en: 'Satellite data products and endpoints' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/services/satellite-intelligence`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/services/satellite-intelligence`, languages: { fa: `${BASE_URL}/fa/public/services/satellite-intelligence`, en: `${BASE_URL}/en/public/services/satellite-intelligence` } },
  };
}

export default async function SatelliteIntelligencePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.services.satelliteIntelligence');
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
          evidence={['Multi-sensor fusion', 'STAC catalog', 'Cloud-optimized COGs']}
          limits={['Cloud masking gaps', 'Atmospheric correction WIP', 'Real-time streaming not live']}
          next={['Add Sentinel-3', 'Enable on-the-fly indices', 'MapLibre integration']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('products')}</h2>
        <div className="grid gap-4">
          {MOCK_PRODUCTS.map(p => (
            <Card key={p.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{p.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {p.status === 'live' ? 'bg-forest/10 text-forest' :
                       p.status === 'beta' ? 'bg-amber/10 text-amber' :
                       'bg-slate/10 text-slate'}">
                      {p.status}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{p.provider} · {p.resolution} · Revisit: {p.revisit}</p>
                  <p className="text-xs text-ink-soft">Bands: {p.bands.join(', ')}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={p.status === 'live' ? 'ok' : p.status === 'beta' ? 'warn' : 'down'} label={common(p.status)} />
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = `/${locale}/public/components/satellite-view`}>{common('demo')}</Button>
                  <ProvenanceStamp source={p.source} verified={true} method="OpenAPI" label={p.status} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}