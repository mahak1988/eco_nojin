import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const MOCK_SPECS = [
  { category: 'Physical', items: [{ label: 'Weight', value: '1 kg' }, { label: 'Dimensions', value: '20x15x5 cm' }, { label: 'Packaging', value: 'Vacuum sealed' }] },
  { category: 'Quality', items: [{ label: 'Grade', value: 'AAA' }, { label: 'Moisture', value: '5.2%' }, { label: 'Defect rate', value: '< 0.5%' }] },
  { category: 'Origin', items: [{ label: 'Region', value: 'Kerman, Iran' }, { label: 'Farm', value: 'Kerman Organic Cooperative' }, { label: 'Harvest', value: '2024-09' }] },
  { category: 'Certifications', items: [{ label: 'Organic', value: 'Yes (EU/USDA)' }, { label: 'Fair Trade', value: 'Certified' }, { label: 'Carbon Neutral', value: 'In progress' }] },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'مشخصات فنی', en: 'Technical Specifications' };
  const descriptions: Record<string, string> = { fa: 'مشخصات کامل محصول', en: 'Complete product specifications' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/specs`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/specs`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/specs`, en: `${BASE_URL}/en/market/product/${id}/specs` } },
  };
}

export default async function SpecsPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.specs');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Product Registry" label={t('provenanceLabel')} verified={true} method="Producer-declared" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        {MOCK_SPECS.map(group => (
          <Card key={group.category} density="compact" className="mb-4">
            <h3 className="font-semibold text-ink mb-3 border-b border-line pb-2">{group.category}</h3>
            <dl className="grid gap-3 sm:grid-cols-2">
              {group.items.map((item, i) => (
                <div key={i} className="flex gap-4">
                  <dt className="text-sm text-ink-soft w-1/2">{item.label}</dt>
                  <dd className="text-sm font-medium text-ink w-1/2">{item.value}</dd>
                </div>
              ))}
            </dl>
          </Card>
        ))}
      </section>
    </main>
  );
}