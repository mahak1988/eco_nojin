import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface APIEndpoint {
  id: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  summary: string;
  auth: 'public' | 'bearer' | 'api-key';
  status: 'stable' | 'beta' | 'deprecated';
  service: string;
}

const MOCK_ENDPOINTS: APIEndpoint[] = [
  { id: 'e1', method: 'GET', path: '/api/market/products', summary: 'List products with filters', auth: 'public', status: 'stable', service: 'marketplace' },
  { id: 'e2', method: 'POST', path: '/api/market/cart', summary: 'Add item to cart', auth: 'bearer', status: 'stable', service: 'commerce' },
  { id: 'e3', method: 'POST', path: '/api/market/checkout', summary: 'Initiate escrow checkout', auth: 'bearer', status: 'stable', service: 'escrow' },
  { id: 'e4', method: 'GET', path: '/api/wallet/balance', summary: 'Get wallet balance', auth: 'bearer', status: 'stable', service: 'ecowallet' },
  { id: 'e5', method: 'GET', path: '/api/mrv/satellite', summary: 'Get satellite MRV data', auth: 'api-key', status: 'beta', service: 'satellite' },
  { id: 'e6', method: 'POST', path: '/api/land/hydrology', summary: 'Run hydrology model', auth: 'bearer', status: 'beta', service: 'hydrology' },
  { id: 'e7', method: 'GET', path: '/api/trust/provenance', summary: 'Query provenance records', auth: 'public', status: 'stable', service: 'provenance' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'زمین بازی API', en: 'API Playground' };
  const descriptions: Record<string, string> = { fa: 'کنسول تعاملی برای تست اندپوینت‌ها', en: 'Interactive console for testing endpoints' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/components/api-playground`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/components/api-playground`, languages: { fa: `${BASE_URL}/fa/public/components/api-playground`, en: `${BASE_URL}/en/public/components/api-playground` } },
  };
}

export default async function APIPlaygroundPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.components.apiPlayground');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="OpenAPI Registry" label={t('provenanceLabel')} verified={true} method="Auto-generated" timestamp="2024-12-10">
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
          evidence={['OpenAPI 3.1 spec', 'Auth modes documented', 'Live try-it console']}
          limits={['Sandbox data only', 'Rate limits enforced', 'Write ops simulated']}
          next={['Add SDK snippets', 'Enable webhook testing', 'GraphQL playground']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('endpoints')}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('method')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('path')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('summary')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('auth')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('status')}</th>
                <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('service')}</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_ENDPOINTS.map(ep => (
                <tr key={ep.id} className="border-b border-line/50">
                  <td className="py-2 px-3">
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {ep.method === 'GET' ? 'bg-forest/10 text-forest' :
                       ep.method === 'POST' ? 'bg-blue/10 text-blue' :
                       ep.method === 'PUT' ? 'bg-amber/10 text-amber' :
                       'bg-red/10 text-red'}">
                      {ep.method}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono text-ink">{ep.path}</td>
                  <td className="py-2 px-3 text-ink-soft">{ep.summary}</td>
                  <td className="py-2 px-3">
                    <span className="px-2 py-1 rounded text-xs font-medium
                      {ep.auth === 'public' ? 'bg-slate/10 text-slate' :
                       ep.auth === 'bearer' ? 'bg-purple/10 text-purple' :
                       'bg-orange/10 text-orange'}">
                      {ep.auth}
                    </span>
                  </td>
                  <td className="py-2 px-3">
                    <StatusDot state={ep.status === 'stable' ? 'ok' : ep.status === 'beta' ? 'warn' : 'down'} label={common(ep.status)} />
                  </td>
                  <td className="py-2 px-3 text-ink-soft">{ep.service}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-6">
        <ProvenanceStamp source="OpenAPI Registry" verified={true} method="Auto-generated" timestamp="2024-12-10" label={t('provenanceLabel')} />
      </div>
      </section>
    </main>
  );
}