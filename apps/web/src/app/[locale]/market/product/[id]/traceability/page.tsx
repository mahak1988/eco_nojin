import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface TraceEvent {
  id: string;
  stage: string;
  location: string;
  date: string;
  actor: string;
  verified: boolean;
  data: string;
}

const MOCK_TRACE: TraceEvent[] = [
  { id: 't1', stage: 'Planting', location: 'Kerman Farm', date: '2024-03-15', actor: 'Farmer Co-op', verified: true, data: 'Organic seed planted' },
  { id: 't2', stage: 'Harvest', location: 'Kerman Farm', date: '2024-09-10', actor: 'Harvest Team', verified: true, data: 'Hand-picked, moisture 5.2%' },
  { id: 't3', stage: 'Processing', location: 'Kerman Facility', date: '2024-09-12', actor: 'Processing Co', verified: true, data: 'Vacuum packed, batch #KMN-2024-0912' },
  { id: 't4', stage: 'Certification', location: 'Tehran Lab', date: '2024-09-20', actor: 'Cert Body', verified: true, data: 'Organic cert #ORG-2024-0456' },
  { id: 't5', stage: 'Shipping', location: 'Bandar Abbas', date: '2024-10-01', actor: 'Logistics Co', verified: false, data: 'Container #MSKU-789456' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'ردیابی و رastreability', en: 'Traceability' };
  const descriptions: Record<string, string> = { fa: 'ردیابی کامل زنجیره تأمین', en: 'Full supply chain traceability' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/traceability`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/traceability`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/traceability`, en: `${BASE_URL}/en/market/product/${id}/traceability` } },
  };
}

export default async function TraceabilityPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.traceability');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Traceability Ledger" label={t('provenanceLabel')} verified={true} method="Blockchain-anchored" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="space-y-4">
          {MOCK_TRACE.map(event => (
            <Card key={event.id} density="compact">
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${event.verified ? 'bg-forest/10' : 'bg-amber/10'}`}>
                  <span className={`text-xl ${event.verified ? 'text-forest' : 'text-amber'}`}>{event.verified ? '✓' : '⟳'}</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-ink">{event.stage}</h3>
                    {event.verified && <span className="px-2 py-0.5 rounded text-xs bg-forest/10 text-forest">{common('verified')}</span>}
                  </div>
                  <p className="text-sm text-ink-soft mt-1">{event.data}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-ink-soft">
                    <span>📍 {event.location}</span>
                    <span>📅 {new Date(event.date).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}</span>
                    <span>👤 {event.actor}</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
        <div className="mt-6">
          <div className="mb-4">
            <ProvenanceStamp source="Traceability Ledger" verified={true} method="On-chain" label={t('ledgerProvenance')} />
          </div>
          <Button variant="primary">{t('downloadCertificate')}</Button>
        </div>
      </section>
    </main>
  );
}