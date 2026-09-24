import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'اثر اکولوژیکی', en: 'Eco Impact' };
  const descriptions: Record<string, string> = { fa: 'شاخص‌های اثر زیست‌محیطی محصول', en: 'Product environmental impact metrics' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/eco-impact`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/eco-impact`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/eco-impact`, en: `${BASE_URL}/en/market/product/${id}/eco-impact` } },
  };
}

export default async function EcoImpactPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.ecoImpact');
  const common = await getTranslations('common');

  const impacts = [
    { key: 'carbon', label: t('carbonSequestration'), value: '12.4 kg CO₂/ha', unit: 'kg CO₂', color: 'forest', verified: true },
    { key: 'water', label: t('waterSavings'), value: '850 L/ha', unit: 'L', color: 'blue', verified: true },
    { key: 'soil', label: t('soilRestoration'), value: '3.2 t/ha', unit: 't/ha', color: 'amber', verified: true },
    { key: 'biodiversity', label: t('biodiversityIndex'), value: '0.78', unit: 'index', color: 'purple', verified: false },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Eco Impact Engine" label={t('provenanceLabel')} verified={true} method="FAO/IPCC models" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {impacts.map(impact => (
            <Card key={impact.key} density="cozy">
              <div className="text-center">
                <div className={`w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center bg-${impact.color}/10`}>
                  <span className={`text-3xl text-${impact.color}`}>
                    {impact.key === 'carbon' ? '🌱' : impact.key === 'water' ? '💧' : impact.key === 'soil' ? '🌱' : '🦋'}
                  </span>
                </div>
                <h3 className="font-semibold text-ink">{impact.label}</h3>
                <p className="text-2xl font-bold text-ink mt-1">{impact.value}</p>
                <p className="text-xs text-ink-soft mt-1">{t('perHectare')}</p>
                <div className="mt-3 flex items-center justify-center gap-1">
                  <span className={`px-2 py-1 rounded text-xs ${impact.verified ? 'bg-forest/10 text-forest' : 'bg-amber/10 text-amber'}`}>
                    {impact.verified ? common('verified') : common('estimated')}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="mt-8">
          <div className="mb-4">
            <ProvenanceStamp source="MRV Data" verified={true} method="Satellite + Ground" label={t('dataProvenance')} />
          </div>
          <Button variant="primary" className="w-full sm:w-auto">{t('downloadReport')}</Button>
        </div>
      </section>
    </main>
  );
}