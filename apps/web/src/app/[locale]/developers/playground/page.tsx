'use client';

import { useTranslations } from 'next-intl';
import { type FormEvent, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

/**
 * Registered session-free read endpoints from the gateway contract. The
 * playground only offers methods the browser can actually complete: the gateway
 * CSRF middleware rejects cookie-less writes, so a POST/PATCH control here
 * would always fail and is not offered.
 */
const READ_ENDPOINTS = [
  '/api/v1/platform/health',
  '/api/v1/platform/stats',
  '/api/v1/platform/landscapes',
  '/api/v1/health',
  '/api/v1/models',
  '/api/v1/models/cpp-status',
  '/api/v1/hydroma/models',
  '/api/v1/hydroma/validation',
  '/api/v1/tool-registry',
  '/api/v1/science/citations/index',
  '/api/v1/science/datasets',
  '/api/v1/science/model-cards',
  '/api/v1/science/zenodo/status',
  '/api/v1/legal-texts',
  '/api/v1/marketplace/products',
  '/api/v1/marketplace/stats',
  '/api/v1/ai/health',
  '/api/v1/voice/health',
  '/api/v1/voice/status',
  '/api/v1/voice/languages',
  '/api/v1/support/personas',
  '/api/v1/content/search?q=soil',
  '/api/v1/mrv/public/dashboard-summary',
  '/api/v1/pilot/stats',
  '/api/v1/manual/status',
];

type Outcome = { status: number; body: string } | null;

export default function PlaygroundPage() {
  const t = useTranslations('developers');
  const common = useTranslations('common');
  const statusPage = useTranslations('statusPage');
  const statusLine = useTranslations('statusLine');
  const template = useTranslations('market.template');

  const [endpoint, setEndpoint] = useState(READ_ENDPOINTS[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [outcome, setOutcome] = useState<Outcome>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setOutcome(null);
    try {
      const res = await fetch(endpoint, {
        method: 'GET',
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      const body = await res.text();
      setOutcome({ status: res.status, body });
    } catch (err) {
      setOutcome({ status: 0, body: err instanceof Error ? err.message : String(err) });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-balance text-4xl font-bold text-ink">{t('title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Card density="cozy">
            <h2 className="field-label">{statusPage('endpoint')}</h2>
            <form onSubmit={handleSubmit} className="mt-3 space-y-4">
              <div>
                <label htmlFor="playground-endpoint" className="sr-only">
                  {statusPage('endpoint')}
                </label>
                <select
                  id="playground-endpoint"
                  value={endpoint}
                  onChange={(event) => setEndpoint(event.target.value)}
                  className="w-full rounded-md border border-line bg-background px-3 py-2 font-mono text-sm text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                >
                  {READ_ENDPOINTS.map((path) => (
                    <option key={path} value={path}>
                      {path}
                    </option>
                  ))}
                </select>
              </div>
              <Button type="submit" size="lg" loading={isLoading} className="w-full">
                {common('view')}
              </Button>
            </form>
          </Card>

          <Card density="cozy">
            <h2 className="field-label">{statusPage('result')}</h2>
            {outcome ? (
              <div className="mt-3 space-y-3">
                <div
                  className={`rounded-md px-3 py-2 font-mono text-sm ${
                    outcome.status >= 200 && outcome.status < 300
                      ? 'bg-forest/10 text-forest'
                      : 'bg-copper/10 text-copper'
                  }`}
                >
                  {statusPage('result')}:{' '}
                  {outcome.status === 0 ? statusLine('unavailable') : outcome.status}
                </div>
                <pre className="max-h-96 overflow-auto rounded-md border border-line bg-surface-2 p-4 font-mono text-xs text-ink">
                  {outcome.body.slice(0, 4000)}
                </pre>
              </div>
            ) : (
              <p className="py-8 text-center text-ink-soft">{statusLine('noData')}</p>
            )}
          </Card>
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="field-label">{template('contractTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{template('contractDescription')}</p>
        </Card>

        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
          </div>
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('nextTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('nextDescription')}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4">
          <Card density="cozy">
            <h3 className="field-label text-clay">{common('limitsLabel')}</h3>
            <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-ink">
              {(t.raw('limits') as string[]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Card>
          <Card density="cozy">
            <h3 className="field-label text-moss">{common('nextLabel')}</h3>
            <ul className="mt-3 space-y-2 text-sm text-ink">
              {(t.raw('next') as string[]).map((item) => (
                <li key={item} className="flex items-baseline gap-2">
                  <span aria-hidden="true" className="text-moss">
                    ↳
                  </span>
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
