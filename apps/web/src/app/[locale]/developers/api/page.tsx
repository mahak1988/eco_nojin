'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface ApiEndpoint {
  method: string;
  path: string;
  summary: string;
  deprecated?: boolean;
}

const ENDPOINTS: ApiEndpoint[] = [
  { method: 'GET', path: '/api/v1/platform/stats', summary: 'Platform statistics' },
  { method: 'GET', path: '/api/v1/platform/landscapes', summary: 'Land profiles list' },
  { method: 'GET', path: '/api/v1/marketplace/products', summary: 'Marketplace products' },
  { method: 'GET', path: '/api/v1/marketplace/stats', summary: 'Marketplace stats' },
  { method: 'POST', path: '/api/v1/ai/assistant', summary: 'AI assistant chat' },
  { method: 'POST', path: '/api/v1/ai/voice', summary: 'AI voice interface' },
  { method: 'GET', path: '/api/v1/trust/provenance', summary: 'Data provenance' },
  { method: 'GET', path: '/api/v1/trust/carbon-registry', summary: 'Carbon registry' },
];

export default function ApiPage() {
  const t = useTranslations('developers.api');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        <Card density="cozy" className="mb-6">
          <h2 className="font-medium text-ink mb-3">{t('baseUrl')}</h2>
          <code className="font-mono text-sm bg-surface-2 border border-line rounded px-3 py-2 block">
            https://api.econojin.example.org
          </code>
          <p className="mt-2 text-sm text-ink-soft">{t('baseUrlNote')}</p>
        </Card>

        <Card density="cozy" className="mb-6">
          <h2 className="font-medium text-ink mb-3">{t('authentication')}</h2>
          <p className="text-sm text-ink-soft mb-3">{t('authNote')}</p>
          <pre className="bg-surface-2 border border-line rounded-md p-4 text-xs font-mono overflow-x-auto text-ink-soft">
            {t('authExample')}
          </pre>
        </Card>

        <Card density="compact">
          <h2 className="font-medium text-ink mb-3">{t('endpoints')}</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line">
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('method')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('path')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('description')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft"></th>
                </tr>
              </thead>
              <tbody>
                {ENDPOINTS.map((ep, idx) => (
                  <tr key={idx} className="border-b border-line/50">
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-mono font-semibold ${
                        ep.method === 'GET' ? 'bg-water/10 text-water' :
                        ep.method === 'POST' ? 'bg-forest/10 text-forest' :
                        'bg-copper/10 text-copper'
                      }`}>
                        {ep.method}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-mono text-ink">{ep.path}</td>
                    <td className="py-2 px-3 text-ink-soft">{ep.summary}</td>
                    <td className="py-2 px-3">
                      {ep.deprecated && (
                        <span className="px-2 py-0.5 rounded text-xs bg-copper/10 text-copper">
                          {t('deprecated')}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <div className="mt-6 grid gap-4">
          <Card density="cozy" className="border-clay/40 bg-clay/5">
            <h3 className="font-medium text-ink mb-2">{t('limitsTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('limits')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-copper">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card density="cozy" className="border-forest/40 bg-forest/5">
            <h3 className="font-medium text-ink mb-2">{t('nextTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('next')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-forest">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </main>
  );
}