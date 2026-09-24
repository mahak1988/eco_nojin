'use client';

import { useState, FormEvent } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Toast } from '@/components/ui/Toast';

export default function PlaygroundPage() {
  const t = useTranslations('developers.playground');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  const [method, setMethod] = useState('GET');
  const [endpoint, setEndpoint] = useState('/api/v1/platform/stats');
  const [headers, setHeaders] = useState('Content-Type: application/json\nAuthorization: Bearer YOUR_TOKEN');
  const [body, setBody] = useState('');
  const [response, setResponse] = useState<{ status: number; data: unknown } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setSubmitStatus('idle');
    setResponse(null);

    try {
      const headerObj: Record<string, string> = {};
      headers.split('\n').forEach(line => {
        const [key, ...valueParts] = line.split(':');
        if (key && valueParts.length) {
          headerObj[key.trim()] = valueParts.join(':').trim();
        }
      });

      const res = await fetch(`https://api.econojin.example.org${endpoint}`, {
        method,
        headers: headerObj,
        body: method !== 'GET' && method !== 'HEAD' ? body : undefined,
      });

      const data = await res.json().catch(() => ({ error: 'Invalid JSON response' }));
      setResponse({ status: res.status, data });
      setSubmitStatus(res.ok ? 'success' : 'error');
    } catch {
      setSubmitStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        {submitStatus === 'success' && (
          <Toast variant="success" title={t('successTitle')} className="mb-6" onClose={() => setSubmitStatus('idle')}>
            {t('successMessage')}
          </Toast>
        )}

        {submitStatus === 'error' && (
          <Toast variant="error" title={t('errorTitle')} className="mb-6" onClose={() => setSubmitStatus('idle')}>
            {t('errorMessage')}
          </Toast>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card density="cozy">
            <h2 className="font-medium text-ink mb-4">{t('request')}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex gap-3">
                <select
                  value={method}
                  onChange={e => setMethod(e.target.value)}
                  className="px-3 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                >
                  {['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={endpoint}
                  onChange={e => setEndpoint(e.target.value)}
                  placeholder="/api/v1/..."
                  className="flex-1 px-4 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ink mb-1">{t('headers')}</label>
                <textarea
                  value={headers}
                  onChange={e => setHeaders(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest font-mono text-sm resize-y"
                  placeholder="Content-Type: application/json&#10;Authorization: Bearer YOUR_TOKEN"
                />
              </div>

              {method !== 'GET' && method !== 'HEAD' && (
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">{t('body')}</label>
                  <textarea
                    value={body}
                    onChange={e => setBody(e.target.value)}
                    rows={6}
                    className="w-full px-4 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest font-mono text-sm resize-y"
                    placeholder='{ "key": "value" }'
                  />
                </div>
              )}

              <Button type="submit" size="lg" disabled={isLoading} className="w-full">
                {isLoading ? t('sending') : t('sendRequest')}
              </Button>
            </form>
          </Card>

          <Card density="cozy">
            <h2 className="font-medium text-ink mb-4">{t('response')}</h2>
            {response ? (
              <div className="space-y-3">
                <div className={`px-3 py-2 rounded-md font-mono text-sm ${
                  response.status >= 200 && response.status < 300
                    ? 'bg-forest/10 text-forest'
                    : 'bg-copper/10 text-copper'
                }`}>
                  Status: {response.status}
                </div>
                <pre className="bg-surface-2 border border-line rounded-md p-4 text-xs font-mono overflow-auto max-h-96 text-ink">
                  {JSON.stringify(response.data, null, 2)}
                </pre>
              </div>
            ) : (
              <p className="text-center text-ink-soft py-8">{t('noResponse')}</p>
            )}
          </Card>
        </div>

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