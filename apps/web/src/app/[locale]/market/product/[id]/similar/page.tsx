import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface SimilarProduct {
  id: string;
  name: { fa: string; en: string };
  producer: string;
  price: number;
  unit: string;
  rating: number;
  similarity: number;
  organic: boolean;
}

const MOCK_SIMILAR: SimilarProduct[] = [
  { id: 'sp1', name: { fa: 'پسته آکبری', en: 'Akbari Pistachio' }, producer: 'Rafsanjan Co-op', price: 285000, unit: '1 kg', rating: 4.9, similarity: 92, organic: true },
  { id: 'sp2', name: { fa: 'پسته احمد آغایی', en: 'Ahmad Aghaei Pistachio' }, producer: 'Kerman Eco', price: 265000, unit: '1 kg', rating: 4.8, similarity: 88, organic: true },
  { id: 'sp3', name: { fa: 'پسته کله قندی', en: 'Kalleh Ghondi Pistachio' }, producer: 'Sirjan Farm', price: 255000, unit: '1 kg', rating: 4.7, similarity: 85, organic: true },
  { id: 'sp4', name: { fa: 'پسته اکبری سوپر', en: 'Super Akbari Pistachio' }, producer: 'Premium Pistachio', price: 320000, unit: '1 kg', rating: 4.95, similarity: 95, organic: true },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'محصولات مشابه', en: 'Similar Products' };
  const descriptions: Record<string, string> = { fa: 'محصولات جایگزین و مشابه', en: 'Alternative and similar products' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/similar`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/similar`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/similar`, en: `${BASE_URL}/en/market/product/${id}/similar` } },
  };
}

export default async function SimilarPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  const loc = locale as string;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.similar');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Recommendation Engine" label={t('provenanceLabel')} verified={true} method="ML similarity" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {MOCK_SIMILAR.map(p => {
            const pName = p.name as Record<string, string>;
            return (
              <Card key={p.id} density="compact">
                <div className="aspect-square flex items-center justify-center bg-slate/10 rounded">
                  📷
                </div>
                <h3 className="font-medium text-ink mt-2 line-clamp-1">{pName[loc] ?? pName.fa}</h3>
                <p className="text-sm text-ink-soft">{p.producer}</p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="font-bold text-forest">{new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(p.price)} ریال / {p.unit}</span>
                  <StatusDot state="ok" label={`${Math.round(p.similarity)}% {t('match')}`} />
                </div>
                {p.organic && <span className="mt-2 inline-block text-xs bg-forest/10 text-forest px-2 py-1 rounded">{common('organic')}</span>}
                <div className="mt-3 flex gap-2">
                  <Button variant="primary" size="sm" className="flex-1" onClick={() => window.location.href = `/${locale}/market/product/${p.id}`}>{common('view')}</Button>
                  <Button variant="ghost" size="sm">{t('compare')}</Button>
                </div>
              </Card>
            );
          })}
        </div>
      </section>
    </main>
  );
}