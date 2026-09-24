import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface License {
  id: string;
  name: string;
  spdx: string;
  component: string;
  type: 'permissive' | 'copyleft' | 'proprietary';
  url: string;
}

const MOCK_LICENSES: License[] = [
  { id: 'l1', name: 'MIT License', spdx: 'MIT', component: 'Frontend UI Kit', type: 'permissive', url: 'https://opensource.org/licenses/MIT' },
  { id: 'l2', name: 'Apache License 2.0', spdx: 'Apache-2.0', component: 'Core Engine (Python)', type: 'permissive', url: 'https://opensource.org/licenses/Apache-2.0' },
  { id: 'l3', name: 'GPL v3.0', spdx: 'GPL-3.0', component: 'CPP Numerical Kernels', type: 'copyleft', url: 'https://www.gnu.org/licenses/gpl-3.0.html' },
  { id: 'l4', name: 'BSD 3-Clause', spdx: 'BSD-3-Clause', component: 'Rust Offline Sync', type: 'permissive', url: 'https://opensource.org/licenses/BSD-3-Clause' },
  { id: 'l5', name: 'Proprietary', spdx: 'Proprietary', component: 'Commercial Extensions', type: 'proprietary', url: 'https://econojin.example.org/license' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'مجوزهای متن‌باز', en: 'Open Source Licenses' };
  const descriptions: Record<string, string> = { fa: 'فهرست مجوزهای مؤلفه‌های پلتفرم', en: 'Platform component license inventory' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/policy/licensing`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/policy/licensing`, languages: { fa: `${BASE_URL}/fa/public/policy/licensing`, en: `${BASE_URL}/en/public/policy/licensing` } },
  };
}

export default async function LicensingPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.policy.licensing');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="License Registry" label={t('provenanceLabel')} verified={true} method="SPDX-compliant" timestamp="2024-12-01">
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
          evidence={['SPDX identifiers', 'Component-level mapping', 'Automated SBOM generation']}
          limits={['Proprietary extensions excluded', 'Dependency scanning partial', 'License compatibility matrix WIP']}
          next={['Full SBOM publishing', 'Automated compliance checks', 'Vulnerability scanning integration']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('licenseTable')}</h2>
        <div className="grid gap-4">
          {MOCK_LICENSES.map(license => (
            <Card key={license.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-ink">{license.name}</h3>
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {license.type === 'permissive' ? 'bg-forest/10 text-forest' :
                       license.type === 'copyleft' ? 'bg-amber/10 text-amber' :
                       'bg-slate/10 text-slate'}">
                      {license.type}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">SPDX: <code className="font-mono">{license.spdx}</code> · {license.component}</p>
                </div>
                <ProvenanceStamp source="SPDX Registry" verified={true} label={license.component} />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}