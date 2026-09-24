'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface WebhookEvent {
  name: string;
  description: string;
  payload: string;
}

const EVENTS: WebhookEvent[] = [
  {
    name: 'order.created',
    description: 'Fired when a new order is placed',
    payload: '{ "orderId": "string", "buyerId": "string", "totalAmount": "number", "currency": "string" }',
  },
  {
    name: 'order.updated',
    description: 'Fired when order status changes',
    payload: '{ "orderId": "string", "previousStatus": "string", "newStatus": "string" }',
  },
  {
    name: 'payment.completed',
    description: 'Fired when escrow payment is released',
    payload: '{ "escrowId": "string", "amount": "number", "currency": "string" }',
  },
  {
    name: 'bazaar.established',
    description: 'Fired when a new bazaar is established',
    payload: '{ "bazaarId": "string", "name": "string", "founders": "string[]" }',
  },
  {
    name: 'carbon.credit.issued',
    description: 'Fired when new carbon credits are minted',
    payload: '{ "projectId": "string", "credits": "number", "vintage": "string" }',
  },
  {
    name: 'user.verified',
    description: 'Fired when a user completes KYC',
    payload: '{ "userId": "string", "level": "string" }',
  },
];

export default function WebhooksPage() {
  const t = useTranslations('developers.webhooks');
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
          <h2 className="font-medium text-ink mb-3">{t('configuration')}</h2>
          <p className="text-sm text-ink-soft mb-3">{t('configNote')}</p>
          <pre className="bg-surface-2 border border-line rounded-md p-4 text-xs font-mono overflow-x-auto text-ink-soft">
            {t('configExample')}
          </pre>
        </Card>

        <Card density="cozy" className="mb-6">
          <h2 className="font-medium text-ink mb-3">{t('security')}</h2>
          <p className="text-sm text-ink-soft mb-3">{t('securityNote')}</p>
          <pre className="bg-surface-2 border border-line rounded-md p-4 text-xs font-mono overflow-x-auto text-ink-soft">
            {t('securityExample')}
          </pre>
        </Card>

        <Card density="compact">
          <h2 className="font-medium text-ink mb-3">{t('events')}</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line">
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('eventName')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('description')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('payload')}</th>
                </tr>
              </thead>
              <tbody>
                {EVENTS.map((evt, idx) => (
                  <tr key={idx} className="border-b border-line/50">
                    <td className="py-2 px-3 font-mono text-ink">{evt.name}</td>
                    <td className="py-2 px-3 text-ink-soft">{evt.description}</td>
                    <td className="py-2 px-3">
                      <pre className="bg-surface-2 border border-line rounded-md p-2 text-[10px] font-mono overflow-x-auto text-ink-soft max-w-xs">
                        {evt.payload}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-3">{t('retryPolicy')}</h2>
          <ul className="space-y-2 text-sm text-ink-soft">
            {t.raw('retryPolicy')?.map((item: string, idx: number) => (
              <li key={idx} className="flex gap-2">
                <span className="text-forest">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
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