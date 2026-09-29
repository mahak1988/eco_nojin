import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

export const dynamic = 'force-dynamic';

/**
 * Inbound webhook receivers that exist in the gateway contract. There is no
 * registered outbound event catalogue, so none is invented here.
 */
const INBOUND_WEBHOOKS = [
  { method: 'POST', path: '/api/v1/mrv/lorawan-webhook' },
  { method: 'POST', path: '/api/v1/finance/payments/webhook/{provider_name}' },
] as const;

export default async function WebhooksPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);
  const t = await getTranslations('developers');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const template = await getTranslations('market.template');

  // The contract is only observable through the gateway schema, so the read
  // surfaces that describe delivery are probed per request.
  const probes = await Promise.all(
    ['/api/v1/health', '/api/v1/finance/idempotency/keys'].map(async (path) => ({
      path,
      reachable: (await apiGet<unknown>(path)).ok,
    })),
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <span className="chip num font-mono">developers/webhooks</span>
        <h1 className="display mt-3 text-4xl font-bold text-ink">{t('title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <StatusDot state="down" label={status('unavailable')} />
          <ProvenanceStamp
            source={statusPage('endpoint')}
            label={statusPage('endpoint')}
            method={statusPage('state')}
          />
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-semibold text-ink">{template('unavailableTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{template('unavailableDescription')}</p>
        </Card>

        <Card density="compact" className="mt-6">
          <h2 className="field-label">{statusPage('label')}</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-ink-soft">
                  <th className="py-2 pe-4 text-start font-medium">{statusPage('endpoint')}</th>
                  <th className="py-2 ps-4 text-start font-medium">{statusPage('state')}</th>
                </tr>
              </thead>
              <tbody>
                {INBOUND_WEBHOOKS.map((hook) => (
                  <tr key={hook.path} className="border-b border-line/50">
                    <td className="py-2 pe-4">
                      <span className="me-2 rounded bg-forest/10 px-2 py-0.5 font-mono text-xs font-semibold text-forest">
                        {hook.method}
                      </span>
                      <span className="font-mono text-xs text-ink">{hook.path}</span>
                    </td>
                    <td className="py-2 ps-4 text-xs text-copper">{status('unavailable')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card density="cozy" className="mt-6">
          <h2 className="field-label">{template('contractTitle')}</h2>
          <ul className="mt-3 grid gap-2">
            {probes.map((probe) => (
              <li key={probe.path} className="flex items-center justify-between gap-3 text-sm">
                <span className="font-mono text-xs text-ink-soft">{probe.path}</span>
                <span className={probe.reachable ? 'text-forest' : 'text-copper'}>
                  {probe.reachable ? common('live') : status('unavailable')}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm text-ink-soft">{template('contractDescription')}</p>
        </Card>

        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('nextTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('nextDescription')}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4">
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
          <ListBlock title={common('next')} items={t.raw('next') as string[]} tone="moss" />
        </div>
      </div>
    </main>
  );
}
