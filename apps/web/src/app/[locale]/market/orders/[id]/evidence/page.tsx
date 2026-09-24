import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'مدرک و مستندات', en: 'Evidence & Documents' };
  const descriptions: Record<string, string> = { fa: 'مدیریت مستندات منازعه', en: 'Manage dispute documents' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/orders/${id}/evidence`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/orders/${id}/evidence`, languages: { fa: `${BASE_URL}/fa/market/orders/${id}/evidence`, en: `${BASE_URL}/en/market/orders/${id}/evidence` } },
  };
}

export default async function EvidencePage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.orders.evidence');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/orders/${id}/dispute`} className="underline hover:text-ink">{common('backToDispute')}</a>
        </nav>
        <ProvenanceStamp source="Evidence Registry" label={t('provenanceLabel')} verified={true} method="Hash-verified" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Hash-verified', 'Immutable storage', 'Access-controlled']}
          limits={['File size limit 50MB', 'Allowed: jpg, png, pdf, mp4', 'Auto-delete after 2 years']}
          next={['Add OCR', 'Enable annotations', 'Version control']}
          evidenceLabel="Evidence" limitsLabel="Limits" nextLabel="Next"
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <div className="flex justify-between mb-6">
          <h2 className="font-semibold text-ink">{t('documents')}</h2>
          <Button variant="primary" className="text-sm">{t('uploadDocument')}</Button>
        </div>

        <div className="grid gap-4">
          {[
            { name: 'receipt.pdf', type: 'pdf', size: '2.4 MB', uploadedBy: 'فروشنده', date: '2024-12-11' },
            { name: 'package_photo.jpg', type: 'image', size: '3.2 MB', uploadedBy: 'فروشنده', date: '2024-12-11' },
            { name: 'delivery_photo.jpg', type: 'image', size: '4.1 MB', uploadedBy: 'خریدار', date: '2024-12-13' },
          ].map((doc, i) => (
            <Card key={i} density="compact">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded flex items-center justify-center bg-slate/10">
                    {doc.type === 'pdf' && '📄'}
                    {doc.type === 'image' && '🖼️'}
                  </div>
                  <div>
                    <p className="font-medium text-ink">{doc.name}</p>
                    <p className="text-xs text-ink-soft">{doc.size} · توسط {doc.uploadedBy} · {doc.date}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm">{t('view')}</Button>
                  <Button variant="ghost" size="sm">{t('download')}</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <Button variant="primary" className="w-full mt-6">{t('submitEvidence')}</Button>
      </section>
    </main>
  );
}