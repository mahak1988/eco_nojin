import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { DataStateCard, SourceFooter, toDataState } from '@/app/[locale]/public/data-states';
import { RecordTable } from '@/components/manual/RecordTable';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import type { ApiResult } from '@/lib/api/client';
import type { ManualRecord } from '@/lib/api/manual';

interface ManualDatasetPageProps {
  locale: string;
  /** The exact path this page fetched, used for provenance and error text. */
  source: string;
  title: string;
  description: string;
  emptyTitle: string;
  emptyDescription: string;
  result: ApiResult<{ count: number }> & { data?: unknown };
  /** Key of the response field that holds the rows, e.g. `rows` or `regions`. */
  rowsKey: string;
  linkColumn?: string;
  hrefFor?: (record: ManualRecord) => string;
  children?: React.ReactNode;
}

function rowsOf(result: ManualDatasetPageProps['result'], rowsKey: string): ManualRecord[] {
  if (!result.ok) return [];
  const data = result.data as Record<string, unknown> | undefined;
  return Array.isArray(data?.[rowsKey]) ? (data?.[rowsKey] as ManualRecord[]) : [];
}

/**
 * Shared shell for the manual reference datasets.
 *
 * It renders exactly one honest state: a real table when the gateway answered,
 * the offline/unavailable state when it did not, and an empty state when the
 * dataset has no rows. Row count, column names and every cell value come from
 * the response, and provenance is verified only for a response that was actually
 * observed.
 */
export async function ManualDatasetPage({
  locale,
  source,
  title,
  description,
  emptyTitle,
  emptyDescription,
  result,
  rowsKey,
  linkColumn,
  hrefFor,
  children,
}: ManualDatasetPageProps) {
  setRequestLocale(locale);
  const t = await getTranslations('manual');
  const rows = rowsOf(result, rowsKey);
  const state = toDataState(source, result, rows.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-6xl px-6 pb-12 pt-8">
        <Link href={`/${locale}/learn/manual/sites`} className="text-sm text-water hover:underline">
          {t('back')}
        </Link>

        <section className="mt-6">
          {/* The heading sits beside the stamp, not inside it: `ProvenanceStamp`
              renders `label ?? children`, so nesting a heading would drop it. */}
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="display text-3xl font-bold text-ink">{title}</h1>
            <ProvenanceStamp source={source} verified={result.ok} method={source} />
          </div>
          <p className="mt-3 max-w-3xl text-ink-soft">{description}</p>
          <p className="num mt-2 break-all text-xs text-ink-faint">{source}</p>
        </section>

        <section className="mt-6">
          <DataStateCard
            state={state}
            emptyTitle={emptyTitle}
            emptyDescription={emptyDescription}
          />
          {state.kind === 'ready' ? (
            <>
              <p className="mt-4 text-xs text-ink-soft">{t('columnNote')}</p>
              <RecordTable
                records={rows}
                caption={t('tableCaption')}
                linkColumn={linkColumn}
                hrefFor={hrefFor}
              />
              {state.count > rows.length ? (
                <p className="num mt-3 text-xs text-ink-soft">
                  {t('truncated', { shown: rows.length, total: state.count })}
                </p>
              ) : null}
            </>
          ) : null}
          <SourceFooter state={state} />
        </section>

        {children}
      </div>
    </main>
  );
}
