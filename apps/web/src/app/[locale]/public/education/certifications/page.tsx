import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Certification {
  id: string;
  title: string;
  issuer: string;
  level: 'foundation' | 'practitioner' | 'expert';
  duration: string;
  prerequisites: string[];
  verified: boolean;
  holders: number;
  source: string;
}

const MOCK_CERTS: Certification[] = [
  { id: 'ct1', title: 'HydroMa Foundation Certificate', issuer: 'HydroMa Academy', level: 'foundation', duration: '40 hours', prerequisites: [], verified: true, holders: 2340, source: 'HydroMa Academy' },
  { id: 'ct2', title: 'Carbon Accounting Practitioner', issuer: 'Verra/GS', level: 'practitioner', duration: '60 hours', prerequisites: ['Foundation Certificate'], verified: true, holders: 567, source: 'Verra' },
  { id: 'ct3', title: 'MRV Expert Certification', issuer: 'ICROA', level: 'expert', duration: '120 hours', prerequisites: ['Practitioner'], verified: false, holders: 89, source: 'ICROA' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'برنامه‌های گواهی', en: 'Certification Programs' };
  const descriptions: Record<string, string> = { fa: 'مسیرهای تخصصی با گواهی‌نامه', en: 'Specialized pathways with certification' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/certifications`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/certifications`, languages: { fa: `${BASE_URL}/fa/public/education/certifications`, en: `${BASE_URL}/en/public/education/certifications` } },
  };
}

export default async function CertificationsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.certifications');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Certification Registry" label={t('provenanceLabel')} verified={true} method="Accredited" timestamp="2024-12-10">
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
          evidence={['Accredited issuers', 'Stackable credentials', 'Digital badges']}
          limits={['Expert level limited', 'Renewal process manual', 'Regional recognition varies']}
          next={['Add micro-credentials', 'Automate renewal', 'University partnerships']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('catalog')}</h2>
        <div className="grid gap-4">
          {MOCK_CERTS.map(cert => (
            <Card key={cert.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{cert.title}</h3>
                  <p className="text-sm text-ink-soft mt-1">{cert.issuer} · {cert.duration} · {cert.holders} {common('holders')}</p>
                  <div className="flex flex-wrap gap-2 mt-2 text-xs">
                    <span className="px-2 py-1 rounded bg-forest/10 text-forest">{cert.level}</span>
                    {cert.prerequisites.map((p, i) => <span key={i} className="px-2 py-1 rounded bg-clay/10 text-clay">{p}</span>)}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={cert.verified ? 'ok' : 'warn'} label={cert.verified ? common('verified') : common('pending')} />
                  <ProvenanceStamp source={cert.source} verified={cert.verified} label={cert.level} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}