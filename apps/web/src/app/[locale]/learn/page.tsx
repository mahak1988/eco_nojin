'use client';

import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { type FormEvent, useCallback, useEffect, useState } from 'react';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

const CONTENT_PATH = '/api/v1/content/search';

type ContentHit = {
  id: string;
  title: string;
  category: string;
  language: string;
  published_at: string | null;
  snippet: string;
};

export default function LearnPage() {
  const t = useTranslations();
  const common = useTranslations('common');
  const statusPage = useTranslations('statusPage');
  const statusLine = useTranslations('statusLine');
  const pathname = usePathname();
  const locale = pathname.split('/')[1] ?? 'fa';

  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<ContentHit[]>([]);
  const [reachable, setReachable] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(
    async (term: string) => {
      setIsLoading(true);
      setError(null);
      try {
        // The registered surface is keyword-only, so an empty term is not a
        // valid query; a single neutral token probes reachability instead.
        const params = new URLSearchParams();
        params.set('q', term || 'a');
        params.set('limit', '20');
        const res = await fetch(`${CONTENT_PATH}?${params.toString()}`, {
          credentials: 'same-origin',
          cache: 'no-store',
        });
        const payload: unknown = await res.json().catch(() => null);
        if (!res.ok) throw new Error(common('error'));
        const parsed = (payload ?? {}) as { results?: unknown };
        setHits(Array.isArray(parsed.results) ? (parsed.results as ContentHit[]) : []);
        setReachable(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : common('error'));
        setReachable(false);
      } finally {
        setIsLoading(false);
      }
    },
    [common],
  );

  useEffect(() => {
    void search('');
  }, [search]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void search(query.trim());
  };

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="display text-balance text-4xl font-bold text-ink">
          {t('learn.emptyTitle')}
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('learn.emptyDesc')}</p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <span className="chip num font-mono">{CONTENT_PATH}</span>
          <StatusDot
            state={reachable ? 'ok' : 'down'}
            label={reachable ? statusLine('realData') : statusLine('unavailable')}
          />
          <span className="num text-xs text-ink-soft">
            {statusPage('result')}: {hits.length}
          </span>
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
              onClick={() => void search(query.trim())}
            >
              {common('retry')}
            </Button>
          </div>
        )}

        <Card density="compact" className="mt-6">
          <form onSubmit={handleSubmit} className="flex flex-wrap gap-3">
            <label htmlFor="learn-query" className="sr-only">
              {statusPage('label')}
            </label>
            <input
              id="learn-query"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="min-w-[240px] flex-1 rounded-md border border-line bg-background px-4 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-forest"
            />
            <Button type="submit" loading={isLoading}>
              {common('view')}
            </Button>
          </form>
        </Card>

        <ul className="mt-6 grid gap-3">
          {hits.length === 0 ? (
            <li>
              <Card density="cozy" className="py-8 text-center">
                <p className="text-ink-soft">{statusLine('noData')}</p>
              </Card>
            </li>
          ) : (
            hits.map((hit) => (
              <li key={hit.id}>
                <Card density="compact">
                  <div className="flex flex-wrap items-baseline justify-between gap-3">
                    <h2 className="text-base font-medium text-ink">{hit.title}</h2>
                    <span className="num text-xs text-ink-soft">
                      {hit.category} · {hit.language}
                      {hit.published_at ? ` · ${hit.published_at.slice(0, 10)}` : ''}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-ink-soft">{hit.snippet}</p>
                </Card>
              </li>
            ))
          )}
        </ul>
      </div>
    </main>
  );
}
