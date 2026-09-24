import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface EngineModule {
  id: string;
  name: string;
  version: string;
  language: string;
  status: 'stable' | 'beta' | 'experimental';
  tests: string;
  coverage: string;
  source: string;
}

const MOCK_MODULES: EngineModule[] = [
  { id: 'm1', name: 'Soil Water Balance (FAO-56)', version: '2.1.0', language: 'Python/C++', status: 'stable', tests: '70/70', coverage: '94%', source: 'engine/hydroma/soil' },
  { id: 'm2', name: 'Surface Hydrology (Saint-Venant)', version: '1.3.0', language: 'C++20', status: 'stable', tests: '45/45', coverage: '89%', source: 'engine/cpp_core/hydro' },
  { id: 'm3', name: 'Erosion (RUSLE2)', version: '2.0.0', language: 'Python', status: 'stable', tests: '38/38', coverage: '91%', source: 'engine/hydroma/erosion' },
  { id: 'm4', name: 'Carbon Cycle (RothC)', version: '1.0.0', language: 'Python', status: 'beta', tests: '22/25', coverage: '78%', source: 'engine/hydroma/carbon' },
  { id: 'm5', name: 'Climate Downscaling', version: '0.9.0', language: 'Python', status: 'experimental', tests: '15/20', coverage: '65%', source: 'engine/hydroma/climate' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'موتور هیدروما', en: 'HydroMa Engine' };
  const descriptions: Record<string, string> = { fa: 'نمایشگر ماژول‌های موتور علمی', en: 'Scientific engine module showcase' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/components/hydroma-engine`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/components/hydroma-engine`, languages: { fa: `${BASE_URL}/fa/public/components/hydroma-engine`, en: `${BASE_URL}/en/public/components/hydroma-engine` } },
  };
}

export default async function HydromaEnginePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.components.hydromaEngine');
  const common = await getTranslations('common');

  const runDemo = (id: string) => alert(`${t('runningDemo')} ${id}`);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Engine Registry" label={t('provenanceLabel')} verified={true} method="CI-validated" timestamp="2024-12-10">
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
          evidence={['FAO/IPCC/OGC compliance', 'C++20 + Python bindings', '70+ unit tests passing']}
          limits={['Experimental modules unstable', 'WASM port partial', 'Regional calibration needed']}
          next={['Complete RothC integration', 'WASM for all modules', 'Add uncertainty quantification']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('modules')}</h2>
        <div className="grid gap-4">
          {MOCK_MODULES.map(mod => (
            <Card key={mod.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{mod.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {mod.status === 'stable' ? 'bg-forest/10 text-forest' :
                       mod.status === 'beta' ? 'bg-amber/10 text-amber' :
                       'bg-purple/10 text-purple'}">
                      {mod.status}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">v{mod.version} · {mod.language} · Tests: {mod.tests} · Coverage: {mod.coverage}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={mod.status === 'stable' ? 'ok' : mod.status === 'beta' ? 'warn' : 'down'} label={common(mod.status)} />
                  <Button variant="ghost" size="sm" onClick={() => runDemo(mod.id)}>{t('runDemo')}</Button>
                  <ProvenanceStamp source={mod.source} verified={true} method="CI" timestamp="2024-12-10" label={mod.version} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}