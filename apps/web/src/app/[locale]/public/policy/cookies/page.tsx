import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Cookie {
  id: string;
  name: string;
  category: 'essential' | 'analytics' | 'preferences' | 'marketing';
  purpose: string;
  duration: string;
  status: 'active' | 'deprecated';
}

const MOCK_COOKIES: Cookie[] = [
  { id: 'ck1', name: 'locale', category: 'essential', purpose: 'Stores language preference', duration: '1 year', status: 'active' },
  { id: 'ck2', name: 'session', category: 'essential', purpose: 'Authentication session', duration: 'Session', status: 'active' },
  { id: 'ck3', name: 'csrf_token', category: 'essential', purpose: 'CSRF protection', duration: 'Session', status: 'active' },
  { id: 'ck4', name: 'analytics_consent', category: 'analytics', purpose: 'Consent for analytics', duration: '1 year', status: 'active' },
  { id: 'ck5', name: '_ga', category: 'analytics', purpose: 'Google Analytics', duration: '2 years', status: 'active' },
  { id: 'ck6', name: 'theme', category: 'preferences', purpose: 'Dark/light mode preference', duration: '1 year', status: 'active' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'سیاست کوکی', en: 'Cookie Policy' };
  const descriptions: Record<string, string> = { fa: 'مدیریت کوکی‌ها و تکنولوژی‌های ردیابی', en: 'Cookie and tracking technology management' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/policy/cookies`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/policy/cookies`, languages: { fa: `${BASE_URL}/fa/public/policy/cookies`, en: `${BASE_URL}/en/public/policy/cookies` } },
  };
}

export default async function CookiesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.policy.cookies');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Cookie Registry" label={t('provenanceLabel')} verified={true} method="Audit-logged" timestamp="2024-12-01">
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
          evidence={['Categorized by purpose', 'Duration specified', 'Consent-managed']}
          limits={['Third-party cookies vary', 'Consent UX not fully granular', 'Audit frequency quarterly']}
          next={['Add cookie scanner', 'Enable granular consent', 'Automated compliance report']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('cookieTable')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('name')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('category')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('purpose')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('duration')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('status')}</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_COOKIES.map(cookie => (
                <tr key={cookie.id} className="border-b border-line/50">
                  <td className="py-2 px-3 font-mono text-ink">{cookie.name}</td>
                  <td className="py-2 px-3">
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {cookie.category === 'essential' ? 'bg-forest/10 text-forest' :
                       cookie.category === 'analytics' ? 'bg-blue/10 text-blue' :
                       cookie.category === 'preferences' ? 'bg-amber/10 text-amber' :
                       'bg-purple/10 text-purple'}">
                      {cookie.category}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-ink-soft">{cookie.purpose}</td>
                  <td className="py-2 px-3 text-ink-soft">{cookie.duration}</td>
                  <td className="py-2 px-3">
                    <StatusDot state={cookie.status === 'active' ? 'ok' : 'down'} label={common(cookie.status)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6">
        <ProvenanceStamp source="Cookie Registry" verified={true} method="Audit-logged" timestamp="2024-12-01" label={t('provenanceLabel')} />
      </div>
      </section>
    </main>
  );
}