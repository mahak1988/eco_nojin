'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface ProvenanceEntry {
  id: string;
  source: string;
  service: string;
  timestamp: string;
  verified: boolean;
  method?: string;
}

export default function ProvenancePage() {
  const t = useTranslations('trust.provenance');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1];

  const [entries, setEntries] = useState<ProvenanceEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProvenance() {
      try {
        const res = await fetch(`/api/trust/provenance?locale=${locale}`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        setEntries(data.entries || []);
      } catch (err) {
        setError(t('fetchError'));
      } finally {
        setIsLoading(false);
      }
    }
    fetchProvenance();
  }, [locale, t]);

  const filteredEntries = entries.filter(e =>
    e.source.toLowerCase().includes(search.toLowerCase()) ||
    e.service.toLowerCase().includes(search.toLowerCase())
  );

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

        <Card density="compact" className="mb-6">
          <div className="flex gap-4">
            <input
              type="search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={t('searchPlaceholder')}
              className="flex-1 px-4 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
              aria-label={t('searchPlaceholder')}
            />
          </div>
        </Card>

        <div className="grid gap-4">
          {filteredEntries.length > 0 ? (
            filteredEntries.map((entry) => (
              <Card key={entry.id} density="compact">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h3 className="font-medium text-ink">{entry.source}</h3>
                    <p className="text-sm text-ink-soft">{entry.service}</p>
                  </div>
                  <ProvenanceStamp
                    source={entry.source}
                    verified={entry.verified}
                    timestamp={entry.timestamp}
                    method={entry.method}
                  />
                </div>
              </Card>
            ))
          ) : (
            <Card density="cozy" className="text-center py-8">
              <p className="text-ink-soft">{t('noResults')}</p>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}