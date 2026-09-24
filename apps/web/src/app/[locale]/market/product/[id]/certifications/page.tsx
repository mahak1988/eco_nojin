import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Certification {
  id: string;
  name: { fa: string; en: string };
  issuer: string;
  status: 'valid' | 'pending' | 'expired';
  issued: string;
  expires: string;
  scope: string;
}

const MOCK_CERTS: Certification[] = [
  { id: 'c1', name: { fa: 'ارگانیک EU', en: 'EU Organic' }, issuer: 'Control Union', status: 'valid', issued: '2024-01-15', expires: '2025-01-14', scope: 'Full production' },
  { id: 'c2', name: { fa: 'ارگانیک USDA', en: 'USDA Organic' }, issuer: 'CCOF', status: 'valid', issued: '2024-02-01', expires: '2025-01-31', scope: 'Full production' },
  { id: 'c3', name: { fa: 'تجارت منصفانه', en: 'Fair Trade' }, issuer: 'FLO-CERT', status: 'pending', issued: '2024-03-01', expires: '2025-03-01', scope: 'Export markets' },
  { id: 'c4', name: { fa: 'کربن خنثی', en: 'Carbon Neutral' }, issuer: 'South Pole', status: 'pending', issued: '2024-06-01', expires: '2025-06-01', scope: 'Product lifecycle' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'گواهی‌نامه‌ها', en: 'Certifications' };
  const descriptions: Record<string, string> = { fa: 'گواهی‌نامه‌های کیفیت و اصالت', en: 'Quality and authenticity certificates' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/certifications`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/certifications`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/certifications`, en: `${BASE_URL}/en/market/product/${id}/certifications` } },
  };
}

export default async function CertificationsPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  const loc = locale as string;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.certifications');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Certification Registry" label={t('provenanceLabel')} verified={true} method="Issuer-verified" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="grid gap-4">
          {MOCK_CERTS.map(cert => {
            const certName = cert.name as Record<string, string>;
            return (
              <Card key={cert.id} density="compact">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-ink">{certName[loc] ?? certName.fa}</h3>
                    <p className="text-sm text-ink-soft mt-1">{cert.issuer} · {cert.scope}</p>
                    <p className="text-xs text-ink-soft">Issued: {cert.issued} · Expires: {cert.expires}</p>
                  </div>
                  <StatusDot
                    state={cert.status === 'valid' ? 'ok' : cert.status === 'pending' ? 'warn' : 'down'}
                    label={common(cert.status)}
                  />
                </div>
              </Card>
            );
          })}
        </div>
        <div className="mt-4">
          <ProvenanceStamp source="Certification Registry" verified={true} method="Issuer API" label={t('provenanceLabel')} />
        </div>
      </section>
    </main>
  );
}