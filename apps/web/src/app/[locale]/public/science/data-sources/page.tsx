import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface DataSource {
  id: string;
  name: string;
  provider: string;
  type: 'satellite' | 'weather' | 'soil' | 'topography' | 'socioeconomic';
  resolution: string;
  coverage: string;
  status: 'active' | 'degraded' | 'maintenance';
  lastUpdate: string;
  license: string;
}

const MOCK_SOURCES: DataSource[] = [
  { id: 'ds1', name: 'Sentinel-2 L2A', provider: 'Copernicus/ESA', type: 'satellite', resolution: '10m', coverage: 'Global', status: 'active', lastUpdate: '2024-12-10', license: 'Open (CC-BY)' },
  { id: 'ds2', name: 'ERA5-Land', provider: 'ECMWF/Copernicus', type: 'weather', resolution: '0.1°', coverage: 'Global', status: 'active', lastUpdate: '2024-12-10', license: 'Open (CC-BY)' },
  { id: 'ds3', name: 'SoilGrids 2.0', provider: 'ISRIC', type: 'soil', resolution: '250m', coverage: 'Global', status: 'active', lastUpdate: '2024-06-15', license: 'CC-BY 4.0' },
  { id: 'ds4', name: 'Copernicus DEM', provider: 'ESA', type: 'topography', resolution: '30m', coverage: 'Global', status: 'active', lastUpdate: '2023-12-01', license: 'Open' },
  { id: 'ds5', name: 'WorldPop 2020', provider: 'WorldPop', type: 'socioeconomic', resolution: '100m', coverage: 'Global', status: 'degraded', lastUpdate: '2020-12-31', license: 'CC-BY 4.0' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'منابع داده', en: 'Data Sources' };
  const descriptions: Record<string, string> = { fa: 'کاتالوگ منابع داده با وضعیت و مجوز', en: 'Data source catalog with status and licensing' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/science/data-sources`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/science/data-sources`, languages: { fa: `${BASE_URL}/fa/public/science/data-sources`, en: `${BASE_URL}/en/public/science/data-sources` } },
  };
}

export default async function DataSourcesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.dataSources');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Data Catalog" label={t('provenanceLabel')} verified={true} method="Catalog-indexed" timestamp="2024-12-10">
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
          evidence={['Open data licenses', 'Provenance tracking', 'Quality flags per source']}
          limits={['Some sources degraded/outdated', 'License compatibility varies', 'Real-time feeds not all live']}
          next={['Add STAC catalog integration', 'Enable automated freshness checks', 'Link to model input requirements']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('sourcesCatalog')}</h2>
        <div className="grid gap-4">
          {MOCK_SOURCES.map(src => (
            <Card key={src.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{src.name}</h3>
                    <span className="text-xs px-2 py-1 rounded bg-forest/10 text-forest">{src.type}</span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{src.provider} · {src.resolution} · {src.coverage}</p>
                  <p className="text-xs text-ink-soft">License: {src.license} · Updated: {src.lastUpdate}</p>
                </div>
                <StatusDot state={src.status === 'active' ? 'ok' : src.status === 'degraded' ? 'warn' : 'down'} label={common(src.status)} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}