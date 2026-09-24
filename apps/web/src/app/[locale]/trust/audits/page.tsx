'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface Audit {
  id: string;
  title: string;
  type: 'certification' | 'audit' | 'compliance';
  status: 'valid' | 'expired' | 'pending';
  issuer: string;
  issuedAt: string;
  expiresAt?: string;
  documentUrl?: string;
}

export default function AuditsPage() {
  const t = useTranslations('trust.audits');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1];

  const [audits, setAudits] = useState<Audit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'valid' | 'expired' | 'pending'>('all');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAudits() {
      try {
        const res = await fetch(`/api/trust/audits?locale=${locale}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        setAudits(data.audits || []);
      } catch (err) {
        setError(t('fetchError'));
      } finally {
        setIsLoading(false);
      }
    }
    fetchAudits();
  }, [locale, t]);

  const filteredAudits = filter === 'all'
    ? audits
    : audits.filter(a => a.status === filter);

  const statusStyles = {
    valid: 'text-forest bg-forest/10',
    expired: 'text-copper bg-copper/10',
    pending: 'text-water bg-water/10',
  };

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

        <div className="mb-6 flex flex-wrap gap-2">
          {(['all', 'valid', 'expired', 'pending'] as const).map((f) => (
            <Button
              key={f}
              variant={filter === f ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setFilter(f)}
            >
              {t(`filter.${f}`)}
            </Button>
          ))}
        </div>

        <div className="grid gap-4">
          {filteredAudits.length > 0 ? (
            filteredAudits.map((audit) => (
              <Card key={audit.id} density="compact">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="font-medium text-ink">{audit.title}</h3>
                    <p className="text-sm text-ink-soft">{audit.issuer}</p>
                    <p className="text-xs text-ink-soft">
                      Issued: {new Date(audit.issuedAt).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}
                      {audit.expiresAt && ` · Expires: ${new Date(audit.expiresAt).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusStyles[audit.status]}`}>
                      {t(`status.${audit.status}`)}
                    </span>
                    {audit.documentUrl && (
                      <a
                        href={audit.documentUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-water hover:underline"
                      >
                        {t('viewDocument')}
                      </a>
                    )}
                    <ProvenanceStamp
                      source={audit.issuer}
                      verified={audit.status === 'valid'}
                      timestamp={audit.issuedAt}
                    />
                  </div>
                </div>
              </Card>
            ))
          ) : (
            <Card density="cozy" className="text-center py-8">
              <p className="text-ink-soft">{t('noAudits')}</p>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}