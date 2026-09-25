'use client';

import { useTranslations } from 'next-intl';
import { type FormEvent, useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

const AGROVOC_PATH = '/api/v1/science/agrovoc';

type AgrovocTerm = { term: string; term_en: string; uri: string; group: string; aliases: string[] };
type AgrovocResponse = {
  count: number | null;
  results: AgrovocTerm[];
  stats?: Record<string, number>;
};

export default function GlossaryPage() {
  const t = useTranslations('ai');
  const common = useTranslations('common');
  const statusPage = useTranslations('statusPage');
  const statusLine = useTranslations('statusLine');

  const [query, setQuery] = useState('');
  const [data, setData] = useState<AgrovocResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (term: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const search = new URLSearchParams();
        if (term) search.set('q', term);
        search.set('limit', '20');
        const res = await fetch(`${AGROVOC_PATH}?${search.toString()}`, {
          credentials: 'same-origin',
          cache: 'no-store',
        });
        const payload: unknown = await res.json().catch(() => null);
        if (!res.ok) throw new Error(common('error'));
        setData(payload as AgrovocResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : common('error'));
      } finally {
        setIsLoading(false);
      }
    },
    [common],
  );

  useEffect(() => {
    void load('');
  }, [load]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void load(query.trim());
  };

  const results = data?.results ?? [];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-balance text-4xl font-bold text-ink">{t('title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className="chip num font-mono">{AGROVOC_PATH}</span>
        </div>

        {error && (
          <div className="mt-6 card border-clay/40 p-4 text-sm" role="alert">
            <p className="font-medium text-clay">{common('error')}</p>
            <p className="mt-1 text-ink-soft">{error}</p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="mt-2"
              onClick={() => void load(query.trim())}
            >
              {common('retry')}
            </Button>
          </div>
        )}

        <Card density="compact" className="mt-6">
          <form onSubmit={handleSubmit} className="flex flex-wrap gap-3">
            <label htmlFor="glossary-query" className="sr-only">
              {statusPage('label')}
            </label>
            <input
              id="glossary-query"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="min-w-[240px] flex-1 rounded-md border border-line bg-background px-4 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-forest"
            />
            <Button type="submit" loading={isLoading}>
              {common('view')}
            </Button>
          </form>
          {data?.stats && (
            <ul className="mt-4 flex flex-wrap gap-2">
              {Object.entries(data.stats).map(([group, value]) => (
                <li key={group} className="chip num font-mono text-[11px]">
                  {group}: {value}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <p className="mt-4 text-sm text-ink-soft">
          {statusPage('result')}: {results.length}
        </p>

        <ul className="mt-3 space-y-3">
          {results.length === 0 ? (
            <li>
              <Card density="cozy" className="py-8 text-center">
                <p className="text-ink-soft">
                  {error ? statusLine('unavailable') : statusLine('noData')}
                </p>
              </Card>
            </li>
          ) : (
            results.map((term) => (
              <li key={term.uri}>
                <Card density="compact">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="text-base font-medium text-ink">{term.term}</h2>
                      <p className="text-sm text-ink-soft">{term.term_en}</p>
                      {term.aliases.length > 0 && (
                        <ul className="mt-2 flex flex-wrap gap-2">
                          {term.aliases.map((alias) => (
                            <li key={alias} className="chip text-[11px]">
                              {alias}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <span className="chip shrink-0 text-[11px]">{term.group}</span>
                  </div>
                  <a
                    href={term.uri}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-block font-mono text-xs text-water hover:underline"
                  >
                    {term.uri}
                  </a>
                </Card>
              </li>
            ))
          )}
        </ul>
      </div>
    </main>
  );
}
