import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface CompareProduct {
  id: string;
  name: { fa: string; en: string };
  producer: string;
  price: number;
  unit: string;
  rating: number;
  organic: boolean;
  certifications: string[];
  ecoImpact: { carbon: number; water: number; soil: number };
  similarity: number;
}

const MOCK_COMPARE: CompareProduct[] = [
  { id: 'p1', name: { fa: 'پسته ارگانیک آکبری', en: 'Organic Akbari Pistachio' }, producer: 'Rafsanjan Organic Co', price: 285000, unit: '1 kg', rating: 4.9, organic: true, certifications: ['Organic', 'Fair Trade'], ecoImpact: { carbon: 12.4, water: 850, soil: 3.2 }, similarity: 95 },
  { id: 'p2', name: { fa: 'پسته احمد آغایی', en: 'Ahmad Aghaei Pistachio' }, producer: 'Kerman Eco Farm', price: 265000, unit: '1 kg', rating: 4.8, organic: true, certifications: ['Organic'], ecoImpact: { carbon: 11.8, water: 820, soil: 3.0 }, similarity: 92 },
  { id: 'p3', name: { fa: 'پسته اکبری سوپر', en: 'Super Akbari Pistachio' }, producer: 'Premium Pistachio', price: 320000, unit: '1 kg', rating: 4.95, organic: true, certifications: ['Organic', 'Fair Trade', 'Carbon Neutral'], ecoImpact: { carbon: 13.1, water: 880, soil: 3.5 }, similarity: 98 },
  { id: 'p4', name: { fa: 'پسته کله قندی', en: 'Kalleh Ghondi Pistachio' }, producer: 'Sirjan Farm', price: 255000, unit: '1 kg', rating: 4.7, organic: true, certifications: ['Organic'], ecoImpact: { carbon: 11.2, water: 800, soil: 2.8 }, similarity: 88 },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'مقایسه محصولات', en: 'Product Comparison' };
  const descriptions: Record<string, string> = { fa: 'مقایسه جنب به جنب تا ۴ محصول', en: 'Side-by-side comparison up to 4 products' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/compare`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/compare`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/compare`, en: `${BASE_URL}/en/market/product/${id}/compare` } },
  };
}

export default async function ComparePage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  const loc = locale as string;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.compare');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-7xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Comparison Engine" label={t('provenanceLabel')} verified={true} method="ML similarity" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-12">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('feature')}</th>
                {MOCK_COMPARE.map(p => {
                  const pName = p.name as Record<string, string>;
                  return (
                    <th key={p.id} className="text-center py-3 px-3">
                      <p className="font-medium text-ink">{pName[loc] ?? pName.fa}</p>
                      <p className="text-xs text-ink-soft">{p.producer}</p>
                      <StatusDot state={p.similarity >= 90 ? 'ok' : p.similarity >= 80 ? 'warn' : 'down'} label={`${Math.round(p.similarity)}% {t('match')}`} />
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('price')}</td>
                {MOCK_COMPARE.map(p => (
                    <td key={p.id} className="py-3 px-3 text-center font-bold text-forest">
                      {new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p.price)} ریال / {p.unit}
                    </td>
                  ))}
              </tr>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('rating')}</td>
                {MOCK_COMPARE.map(p => (
                    <td key={p.id} className="py-3 px-3 text-center">{'★'.repeat(Math.floor(p.rating))} {p.rating}</td>
                  ))}
              </tr>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('organic')}</td>
                {MOCK_COMPARE.map(p => (
                    <td key={p.id} className="py-3 px-3 text-center">
                      {p.organic ? <span className="px-2 py-1 rounded bg-forest/10 text-forest text-xs">{common('yes')}</span> : <span className="px-2 py-1 rounded bg-amber/10 text-amber text-xs">{common('no')}</span>}
                    </td>
                  ))}
              </tr>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('certifications')}</td>
                {MOCK_COMPARE.map(p => (
                  <td key={p.id} className="py-3 px-3 text-center">
                    <div className="flex flex-wrap gap-1 justify-center">
                      {p.certifications.map(c => <span key={c} className="px-2 py-1 rounded bg-amber/10 text-amber text-xs">{c}</span>)}
                    </div>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('carbonImpact')}</td>
                {MOCK_COMPARE.map(p => (
                  <td key={p.id} className="py-3 px-3 text-center text-forest">{p.ecoImpact.carbon} kg CO₂</td>
                ))}
              </tr>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('waterImpact')}</td>
                {MOCK_COMPARE.map(p => (
                  <td key={p.id} className="py-3 px-3 text-center text-blue">{p.ecoImpact.water} L</td>
                ))}
              </tr>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('soilImpact')}</td>
                {MOCK_COMPARE.map(p => (
                  <td key={p.id} className="py-3 px-3 text-center text-amber">{p.ecoImpact.soil} t/ha</td>
                ))}
              </tr>
              <tr className="border-b border-line/50">
                <td className="py-3 px-3 font-medium text-ink">{t('actions')}</td>
                {MOCK_COMPARE.map(p => (
                  <td key={p.id} className="py-3 px-3 text-center">
                    <div className="flex gap-1 justify-center">
                      <Button variant="primary" size="sm" onClick={() => window.location.href = `/${locale}/market/product/${p.id}`}>{common('view')}</Button>
                      <Button variant="ghost" size="sm">{t('addToCompare')}</Button>
                    </div>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-ink-soft">{t('antiFraudWarning')}</p>
        </div>

        <div className="mt-4">
          <ProvenanceStamp source="Comparison Engine" verified={true} method="ML similarity" label={t('provenanceLabel')} />
        </div>
      </section>
    </main>
  );
}