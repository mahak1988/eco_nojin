'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';

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

const MOCK_ESCROW: EscrowData = {
  id: 'ESC-001',
  product: 'Organic Pistachio Kernels',
  amount: 514500,
  currency: 'IRT',
  status: 'released',
  createdAt: '2025-09-15T10:35:00Z',
  updatedAt: '2025-09-18T10:00:00Z',
  orderId: 'ORD-001',
  contractHash: '0x8a4f...c2d3',
  parties: [
    { role: 'buyer', name: 'Eco Buyer', address: '0x1a4f...', signed: true, timestamp: '2025-09-15T10:35:00Z' },
    { role: 'seller', name: 'Kerman Cooperative', address: '0x2b8c...', signed: true, timestamp: '2025-09-15T10:36:00Z' },
    { role: 'arbitrator', name: 'Platform Arbitration', address: '0x3d2e...', signed: false },
    { role: 'platform', name: 'Eco Nojin', address: '0x4f1a...', signed: true, timestamp: '2025-09-15T10:35:00Z' },
  ],
  events: [
    {
      id: 'ev1',
      timestamp: '2025-09-15T10:35:00Z',
      action: 'created',
      description: 'Escrow contract deployed',
      party: 'Platform',
      signature: 'PQ-DILITHIUM2',
    },
    {
      id: 'ev2',
      timestamp: '2025-09-15T10:35:30Z',
      action: 'locked',
      description: 'Funds locked by 4-of-5 parties',
      party: 'Buyer',
      signature: 'ED25519',
    },
    {
      id: 'ev3',
      timestamp: '2025-09-16T14:00:00Z',
      action: 'shipped',
      description: 'Shipment confirmed by seller',
      party: 'Seller',
      signature: 'ED25519',
    },
    {
      id: 'ev4',
      timestamp: '2025-09-18T09:20:00Z',
      action: 'confirmed',
      description: 'Delivery confirmed by buyer',
      party: 'Buyer',
      signature: 'ED25519',
    },
    {
      id: 'ev5',
      timestamp: '2025-09-18T10:00:00Z',
      action: 'released',
      description: 'Funds released to seller',
      party: 'Platform',
      signature: 'PQ-KYBER512',
    },
  ],
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
};

export default function EscrowPage({ params }: { params: Promise<{ id: string }> }) {
  const t = useTranslations('market.escrow');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const [escrow, setEscrow] = useState<EscrowData>(MOCK_ESCROW);
  const [showConfirm, setShowConfirm] = useState(false);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const handleRelease = () => {
    setShowConfirm(false);
    alert(t('released'));
  };

  const handleCancel = () => {
    setShowConfirm(false);
    alert(t('cancelled'));
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

        <Card density="compact" className="mb-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-ink-soft">{t('amount')}</p>
              <p className="text-2xl font-bold text-forest">{formatPrice(escrow.amount)} ریال</p>
            </div>
            <StatusDot
              state={statusStateMap[escrow.status] || 'ok'}
              label={escrow.status}
            />
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
            {escrow.parties.map(party => (
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
            {escrow.events.map(event => (
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
                    <span className="text-xs text-forest">
                      {event.signature}
                    </span>
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

        {escrow.status !== 'released' && escrow.status !== 'cancelled' && escrow.status !== 'disputed' && (
          <div className="mt-6 flex gap-3">
            <Button variant="primary" onClick={() => setShowConfirm(true)}>
              {t('releaseFunds')}
            </Button>
            <Button variant="danger" onClick={handleCancel}>
              {t('cancelEscrow')}
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
            source="Escrow Service"
            verified={true}
            method="5-party PQ signature"
            label={t('escrowProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}
