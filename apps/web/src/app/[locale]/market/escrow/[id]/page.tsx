'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { use, useEffect, useState } from 'react';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { getEscrowStatus, openDispute, settleOrder } from '@/lib/api/escrow';

interface EscrowParty {
  role: 'buyer' | 'seller' | 'arbitrator' | 'platform';
  name: string;
  address: string;
  signed: boolean;
  timestamp?: string;
}

interface EscrowEvent {
  id: string;
  timestamp: string;
  action: string;
  description: string;
  party: string;
  signature?: string;
}

interface EscrowData {
  id: string;
  product: string;
  amount: number;
  currency: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  parties: EscrowParty[];
  events: EscrowEvent[];
  contractHash: string;
  orderId: string;
}

const EMPTY_ESCROW: EscrowData = {
  id: '',
  product: '',
  amount: 0,
  currency: '',
  status: 'unavailable',
  createdAt: '',
  updatedAt: '',
  orderId: '',
  contractHash: '',
  parties: [],
  events: [],
};

const statusStateMap: Record<string, 'ok' | 'warn' | 'down'> = {
  created: 'ok',
  locked: 'ok',
  shipped: 'ok',
  confirmed: 'ok',
  released: 'ok',
  disputed: 'down',
  cancelled: 'down',
  pending: 'warn',
  unavailable: 'warn',
};

export default function EscrowPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations('market.escrow');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const [escrow, setEscrow] = useState<EscrowData>(EMPTY_ESCROW);
  const [showConfirm, setShowConfirm] = useState(false);
  const [dataState, setDataState] = useState<'loading' | 'live' | 'unavailable'>('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    void getEscrowStatus(id).then((result) => {
      if (!active) return;
      if (result.ok) {
        setEscrow((current) => ({ ...current, id, status: result.data.escrow_status }));
        setDataState('live');
      } else {
        setDataState('unavailable');
        setError(result.error);
      }
    });
    return () => {
      active = false;
    };
  }, [id]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const handleRelease = async () => {
    if (!escrow.orderId) {
      setError(t('dataUnavailable'));
      return;
    }
    setShowConfirm(false);
    const result = await settleOrder(escrow.orderId);
    if (result.ok) {
      setEscrow((current) => ({ ...current, status: 'released' }));
    } else {
      setError(result.error);
    }
  };

  const handleDispute = async () => {
    if (!escrow.orderId) {
      setError(t('dataUnavailable'));
      return;
    }
    const result = await openDispute(escrow.orderId);
    if (result.ok) {
      setEscrow((current) => ({ ...current, status: 'disputed' }));
    } else {
      setError(result.error);
    }
  };

  const roleLabels: Record<string, string> = {
    buyer: t('buyer'),
    seller: t('seller'),
    arbitrator: t('arbitrator'),
    platform: t('platform'),
  };

  const handleBack = () => {
    router.push(`/${locale}/market/orders`);
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <button
              type="button"
              onClick={handleBack}
              className="text-sm text-ink-soft hover:text-ink underline"
            >
              {common('back')}
            </button>
          </nav>
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
            {t('title')}: {escrow.id}
          </h1>
          <p className="mt-2 text-ink-soft">{escrow.product}</p>
        </header>

        {dataState === 'unavailable' && (
          <p
            role="status"
            className="mb-6 rounded-md border border-line bg-surface-alt p-3 text-sm text-ink-soft"
          >
            {t('dataUnavailable')}
          </p>
        )}
        {error && (
          <p role="alert" className="mb-6 rounded-md bg-red-50 p-3 text-sm text-red-800">
            {error}
          </p>
        )}

        <Card density="compact" className="mb-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-ink-soft">{t('amount')}</p>
              <p className="text-2xl font-bold text-forest">{formatPrice(escrow.amount)} ریال</p>
            </div>
            <StatusDot state={statusStateMap[escrow.status] || 'ok'} label={escrow.status} />
          </div>
          <div className="mt-4">
            <p className="text-xs text-ink-soft">
              {t('contractHash')}: <code className="text-ink">{escrow.contractHash}</code>
            </p>
            <p className="text-xs text-ink-soft mt-1">
              {t('orderId')}: {escrow.orderId}
            </p>
          </div>
        </Card>

        <Card density="compact" className="mb-6">
          <h2 className="font-medium text-ink mb-3">{t('parties')}</h2>
          <div className="space-y-3">
            {escrow.parties.map((party) => (
              <div key={party.role} className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-ink">{roleLabels[party.role]}</p>
                  <p className="text-sm text-ink-soft">{party.name}</p>
                  <p className="text-xs text-ink-soft font-mono">{party.address}</p>
                </div>
                <StatusDot
                  state={party.signed ? 'ok' : 'warn'}
                  label={party.signed ? t('signed') : t('notSigned')}
                />
              </div>
            ))}
          </div>
        </Card>

        <Card density="compact" className="mb-6">
          <h2 className="font-medium text-ink mb-4">{t('eventTimeline')}</h2>
          <div className="space-y-4">
            {escrow.events.map((event) => (
              <div key={event.id} className="border-l-2 border-forest pl-4 pb-2 relative">
                <div className="absolute -left-[5px] top-0 h-3 w-3 rounded-full bg-forest" />
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-ink">{event.action}</p>
                    <p className="text-sm text-ink-soft">{event.description}</p>
                    <p className="text-xs text-ink-soft mt-1">
                      {new Date(event.timestamp).toLocaleString()} • {event.party}
                    </p>
                  </div>
                  {event.signature && (
                    <span className="text-xs text-forest">{event.signature}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {escrow.status === 'released' && (
          <Card density="compact" className="mb-6">
            <p className="text-ink-soft text-sm">{t('escrowComplete')}</p>
          </Card>
        )}

        {escrow.status !== 'released' &&
          escrow.status !== 'cancelled' &&
          escrow.status !== 'disputed' && (
            <div className="mt-6 flex gap-3">
              <Button
                variant="primary"
                disabled={!escrow.orderId}
                onClick={() => setShowConfirm(true)}
              >
                {t('releaseFunds')}
              </Button>
              <Button variant="danger" disabled={!escrow.orderId} onClick={handleDispute}>
                {t('openDispute')}
              </Button>
            </div>
          )}

        {showConfirm && (
          <Card density="cozy" className="mt-4">
            <h3 className="font-medium text-ink mb-2">{t('confirmRelease')}</h3>
            <p className="text-sm text-ink-soft mb-4">{t('confirmReleaseDesc')}</p>
            <div className="flex gap-3">
              <Button variant="primary" size="sm" onClick={handleRelease}>
                {t('confirmReleaseButton')}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowConfirm(false)}>
                {common('cancel')}
              </Button>
            </div>
          </Card>
        )}

        <Card density="compact" className="mt-8">
          <ProvenanceStamp
            source={`/api/v1/marketplace/payments/${encodeURIComponent(id)}/escrow`}
            verified={false}
            label={t('escrowProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}
