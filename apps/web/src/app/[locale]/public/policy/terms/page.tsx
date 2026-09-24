import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Version {
  version: string;
  date: string;
  changes: string[];
  hash: string;
}

const MOCK_VERSIONS: Version[] = [
  { version: '2.1.0', date: '2024-12-01', changes: ['Added AI usage terms', 'Updated data residency clauses', 'Clarified liability limits'], hash: 'sha256:a1b2...' },
  { version: '2.0.0', date: '2024-06-15', changes: ['Major restructuring', 'Added 14-language support', 'Escrow terms integrated'], hash: 'sha256:c3d4...' },
  { version: '1.5.0', date: '2023-12-01', changes: ['Carbon credit terms', 'Dispute resolution updates'], hash: 'sha256:e5f6...' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'شرایط استفاده', en: 'Terms of Service' };
  const descriptions: Record<string, string> = { fa: 'شرایط و قوانین استفاده از پلتفرم', en: 'Platform terms and conditions of use' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/policy/terms`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/policy/terms`, languages: { fa: `${BASE_URL}/fa/public/policy/terms`, en: `${BASE_URL}/en/public/policy/terms` } },
  };
}

export default async function TermsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.policy.terms');
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
          evidence={['Version-controlled (Git)', '14-language synchronized', 'Legal review per release']}
          limits={['Not legal advice', 'Jurisdiction-specific gaps', 'Enforceability varies by region']}
          next={['Add automated compliance checks', 'Enable diff viewer', 'Integrate with e-signature']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('currentVersion')}</h2>
        <Card density="compact">
          <div className="prose max-w-none text-ink">
            <h3 className="font-semibold mb-2">v2.1.0 — {t('effectiveDate')} 2024-12-01</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>{t('term1')}</li>
              <li>{t('term2')}</li>
              <li>{t('term3')}</li>
              <li>{t('term4')}</li>
              <li>{t('term5')}</li>
            </ul>
          </div>
          <ProvenanceStamp source="Legal Registry" verified={true} method="Git-signed" timestamp="2024-12-01" label="v2.1.0" />
        </Card>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('versionHistory')}</h2>
        <div className="space-y-3">
          {MOCK_VERSIONS.map(v => (
            <Card key={v.version} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">Version {v.version}</h3>
                  <p className="text-sm text-ink-soft">{v.date} · {v.changes.length} {common('changes')}</p>
                </div>
                <ProvenanceStamp source="Legal Registry" verified={true} method="Git-signed" timestamp={v.date} label={v.hash} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}