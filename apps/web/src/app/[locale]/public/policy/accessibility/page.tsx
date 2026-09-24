import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface A11yCheck {
  id: string;
  criterion: string;
  level: 'A' | 'AA' | 'AAA';
  status: 'pass' | 'fail' | 'partial';
  description: string;
}

const MOCK_CHECKS: A11yCheck[] = [
  { id: 'a1', criterion: '1.1.1 Non-text Content', level: 'A', status: 'pass', description: 'All images have alt text; icons have aria-label' },
  { id: 'a2', criterion: '1.3.1 Info and Relationships', level: 'A', status: 'pass', description: 'Semantic HTML; heading hierarchy correct' },
  { id: 'a3', criterion: '1.4.3 Contrast (Minimum)', level: 'AA', status: 'pass', description: 'All text meets 4.5:1; large text 3:1' },
  { id: 'a4', criterion: '1.4.11 Non-text Contrast', level: 'AA', status: 'partial', description: 'Most UI components meet 3:1; some charts need review' },
  { id: 'a5', criterion: '2.1.1 Keyboard', level: 'A', status: 'pass', description: 'All functionality keyboard accessible' },
  { id: 'a6', criterion: '2.4.7 Focus Visible', level: 'AA', status: 'pass', description: 'Focus indicators meet 3:1 contrast' },
  { id: 'a7', criterion: '3.1.1 Language of Page', level: 'A', status: 'pass', description: 'lang/dir set per locale; 14 languages supported' },
  { id: 'a8', criterion: '4.1.2 Name, Role, Value', level: 'A', status: 'partial', description: 'Custom components need ARIA review' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'بيان دسترس‌پذیری', en: 'Accessibility Statement' };
  const descriptions: Record<string, string> = { fa: 'تعهد به WCAG 2.2 AA و وضعیت انطباق', en: 'Commitment to WCAG 2.2 AA and conformance status' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/policy/accessibility`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/policy/accessibility`, languages: { fa: `${BASE_URL}/fa/public/policy/accessibility`, en: `${BASE_URL}/en/public/policy/accessibility` } },
  };
}

export default async function AccessibilityPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.policy.accessibility');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Accessibility Audit" label={t('provenanceLabel')} verified={true} method="WCAG 2.2 AA" timestamp="2024-12-10">
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
          evidence={['WCAG 2.2 AA target', 'Automated axe-core CI', 'Manual keyboard testing', 'Screen reader testing (NVDA/VoiceOver)']}
          limits={['Dynamic content gaps', 'Third-party embed issues', 'RTL bidi edge cases', 'PDF accessibility not audited']}
          next={['Schedule quarterly audits', 'Add user testing panel', 'Fix partial criteria', 'PDF remediation pipeline']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="flex gap-4 mb-6">
          <StatusDot state="ok" label={`${MOCK_CHECKS.filter(c => c.status === 'pass').length} Pass`} />
          <StatusDot state="warn" label={`${MOCK_CHECKS.filter(c => c.status === 'partial').length} Partial`} />
          <StatusDot state="down" label={`${MOCK_CHECKS.filter(c => c.status === 'fail').length} Fail`} />
        </div>
        <h2 className="text-xl font-semibold text-ink mb-4">{t('criteriaTable')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('criterion')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('level')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('status')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('description')}</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_CHECKS.map(check => (
                <tr key={check.id} className="border-b border-line/50">
                  <td className="py-2 px-3 font-mono text-ink">{check.criterion}</td>
                  <td className="py-2 px-3"><span className="px-2 py-1 rounded text-xs font-medium bg-slate/10 text-slate">{check.level}</span></td>
                  <td className="py-2 px-3">
                    <StatusDot state={check.status === 'pass' ? 'ok' : check.status === 'partial' ? 'warn' : 'down'} label={common(check.status)} />
                  </td>
                  <td className="py-2 px-3 text-ink-soft">{check.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6">
        <ProvenanceStamp source="Accessibility Audit" verified={true} method="WCAG 2.2 AA" timestamp="2024-12-10" label={t('provenanceLabel')} />
      </div>
      </section>
    </main>
  );
}