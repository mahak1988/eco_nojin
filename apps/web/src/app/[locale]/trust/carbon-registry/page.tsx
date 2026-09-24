'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface CarbonTransaction {
  id: string;
  txHash: string;
  blockNumber: number;
  amount: number;
  token: string;
  timestamp: string;
  verified: boolean;
}

export default function CarbonRegistryPage() {
  const t = useTranslations('trust.carbonRegistry');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1];

  const [transactions, setTransactions] = useState<CarbonTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRegistry() {
      try {
        const res = await fetch(`/api/trust/carbon-registry?locale=${locale}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        setTransactions(data.transactions || []);
      } catch (err) {
        setError(t('fetchError'));
      } finally {
        setIsLoading(false);
      }
    }
    fetchRegistry();
  }, [locale, t]);

  const formatTxHash = (hash: string) => `${hash.slice(0, 10)}...${hash.slice(-8)}`;

  if (isLoading) {
    return (
      <main id="main" className="min-h-screen">
        <div className="mx-auto max-w-4xl px-4 py-10">
          <div className="text-center py-20">
            <p className="text-ink-soft">{t('loading')}</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded-md bg-red-50 border border-red-200 text-red-700" role="alert">
            {error}
            <Button variant="ghost" size="sm" className="ml-2" onClick={() => router.refresh()}>
              Try again
            </Button>
          </div>
        )}

        <div className="grid gap-4">
          {transactions.length > 0 ? (
            transactions.map((tx) => (
              <Card key={tx.id} density="compact">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="font-mono text-sm text-ink">{formatTxHash(tx.txHash)}</p>
                      <p className="text-xs text-ink-soft">Block #{tx.blockNumber.toLocaleString()}</p>
                    </div>
                    <div className="ml-4 border-l border-line pl-4">
                      <p className="font-mono text-lg font-semibold text-forest">
                        {tx.amount.toLocaleString()} {tx.token}
                      </p>
                      <p className="text-xs text-ink-soft">{new Date(tx.timestamp).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}</p>
                    </div>
                  </div>
                  <ProvenanceStamp
                    source="Blockchain"
                    verified={tx.verified}
                    timestamp={tx.timestamp}
                    method="Smart Contract"
                  />
                </div>
              </Card>
            ))
          ) : (
            <Card density="cozy" className="text-center py-8">
              <p className="text-ink-soft">{t('noTransactions')}</p>
            </Card>
          )}
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-3">{t('verificationNote')}</h2>
          <p className="text-sm text-ink-soft">{t('verificationNoteDesc')}</p>
          <div className="mt-4 flex gap-2">
            <a
              href="https://explorer.example.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-water hover:underline"
            >
              {t('viewOnExplorer')}
            </a>
          </div>
        </Card>
      </div>
    </main>
  );
}