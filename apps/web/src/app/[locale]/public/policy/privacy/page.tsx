import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface PrivacySection {
  id: string;
  title: string;
  content: string;
  lastUpdated: string;
  source: string;
}

const MOCK_SECTIONS: PrivacySection[] = [
  { id: 'p1', title: 'Data Controller', content: 'Eco Nojin Foundation is the data controller for personal data processed through this platform.', lastUpdated: '2024-12-01', source: 'Legal Registry' },
  { id: 'p2', title: 'Categories of Personal Data', content: 'We process: account data, land profile data, transaction data, usage analytics, and communication preferences.', lastUpdated: '2024-12-01', source: 'Legal Registry' },
  { id: 'p3', title: 'Legal Basis', content: 'Processing is based on: contract performance, legitimate interest, consent, and legal obligations.', lastUpdated: '2024-12-01', source: 'Legal Registry' },
  { id: 'p4', title: 'Data Retention', content: 'Account data: 7 years post-closure. Transaction data: 10 years (financial regulation). Analytics: 2 years anonymized.', lastUpdated: '2024-12-01', source: 'Legal Registry' },
  { id: 'p5', title: 'Your Rights', content: 'Access, rectification, erasure, restriction, portability, objection, and complaint to supervisory authority.', lastUpdated: '2024-12-01', source: 'Legal Registry' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'حریم خصوصی', en: 'Privacy Policy' };
  const descriptions: Record<string, string> = { fa: 'سیاست حفاظت از داده‌های شخصی', en: 'Personal data protection policy' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/policy/privacy`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/policy/privacy`, languages: { fa: `${BASE_URL}/fa/public/policy/privacy`, en: `${BASE_URL}/en/public/policy/privacy` } },
  };
}

export default async function PrivacyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.policy.privacy');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Legal Registry" label={t('provenanceLabel')} verified={true} method="Version-controlled" timestamp="2024-12-01">
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
          evidence={['GDPR/CCPA aligned', 'Data minimization by design', 'Annual DPIA reviews']}
          limits={['Regional law variations', 'Cross-border transfer complexity', 'AI processing not fully covered']}
          next={['Add automated DSAR handling', 'Enable data portability API', 'Regional compliance dashboards']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        {MOCK_SECTIONS.map(section => (
          <Card key={section.id} density="compact" className="mb-4">
            <h3 className="font-semibold text-ink mb-2">{section.title}</h3>
            <div className="prose max-w-none text-ink-soft">{section.content}</div>
            <ProvenanceStamp source={section.source} verified={true} method="Legal review" timestamp={section.lastUpdated} />
          </Card>
        ))}
      </section>
    </main>
  );
}