import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import {
  WorkspaceDataGrid,
  type WorkspaceGridColumn,
} from '@/components/workspace/WorkspaceDataGrid';
import { WorkspacePageHeader } from '@/components/workspace/WorkspacePageHeader';
import {
  WorkspaceCapabilityTable,
  WorkspaceScopeNote,
  WorkspaceSourceNote,
  WorkspaceUnavailable,
} from '@/components/workspace/WorkspaceStates';
import { formatTimestamp, readContentHits, readDocuments } from '@/lib/workspaces/data';
import { accessRole, authorizeWorkspace, workspaceToken } from '@/lib/workspaces/guard';
import {
  getWorkspacePage,
  WORKSPACE_CONTENT_SEARCH_ENDPOINT,
  WORKSPACE_LEGAL_TEXTS_ENDPOINT,
  workspacePageHref,
} from '@/lib/workspaces/registry';
import { workspaceGet } from '@/lib/workspaces/server';

// Published documents and search hits are read from the gateway per request.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('knowledge');

/** The search contract requires a non-empty query, so it is only called with one. */
const MAX_QUERY_LENGTH = 200;

function firstValue(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? (value[0] ?? '') : (value ?? '');
  return raw.trim().slice(0, MAX_QUERY_LENGTH);
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t(PAGE.labelKey),
    description: t(PAGE.leadKey),
    robots: { index: false, follow: false },
  };
}

export default async function KnowledgePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const query = await searchParams;
  setRequestLocale(locale);
  const t = await getTranslations();

  const access = await authorizeWorkspace();
  const token = workspaceToken(access.status === 'authorized' ? access.session : null);
  const search = firstValue(query.q);

  const documents = await workspaceGet<unknown>(token, WORKSPACE_LEGAL_TEXTS_ENDPOINT);
  // Only a non-empty query reaches the search contract, so the page never
  // manufactures a result set from an absent request.
  const hits =
    search === ''
      ? null
      : await workspaceGet<unknown>(
          token,
          `${WORKSPACE_CONTENT_SEARCH_ENDPOINT}?q=${encodeURIComponent(search)}&limit=10`,
        );

  const documentRows = documents.ok ? readDocuments(documents.data) : [];
  const hitRows = hits?.ok ? readContentHits(hits.data) : [];
  const notProvided = t('auth.session.unknown');

  const documentColumns: readonly WorkspaceGridColumn<(typeof documentRows)[number]>[] = [
    {
      id: 'title',
      labelKey: 'statusPage.label',
      search: (row) => row.title,
      compare: (a, b) => a.title.localeCompare(b.title),
      render: (row) => <span className="font-medium text-ink">{row.title}</span>,
    },
    {
      id: 'locale',
      labelKey: 'auth.session.language',
      search: (row) => row.locale,
      compare: (a, b) => a.locale.localeCompare(b.locale),
      render: (row) => <span className="num text-xs text-ink-soft">{row.locale}</span>,
    },
    {
      id: 'slug',
      labelKey: 'statusPage.endpoint',
      search: (row) => row.slug,
      compare: (a, b) => a.slug.localeCompare(b.slug),
      render: (row) => <span className="num break-all text-xs text-ink-soft">{row.slug}</span>,
    },
    {
      id: 'version',
      labelKey: 'legal.version',
      numeric: true,
      compare: (a, b) => a.version - b.version,
      render: (row) => <span className="num">{row.version}</span>,
    },
    {
      id: 'effective',
      labelKey: 'common.live',
      search: (row) => row.effectiveAt ?? '',
      compare: (a, b) => (a.effectiveAt ?? '').localeCompare(b.effectiveAt ?? ''),
      render: (row) => (
        <span className="num text-xs text-ink-soft">
          {formatTimestamp(row.effectiveAt, locale, notProvided)}
        </span>
      ),
    },
  ];

  const hitColumns: readonly WorkspaceGridColumn<(typeof hitRows)[number]>[] = [
    {
      id: 'hit-title',
      labelKey: 'statusPage.label',
      search: (row) => row.title,
      compare: (a, b) => a.title.localeCompare(b.title),
      render: (row) => <span className="font-medium text-ink">{row.title}</span>,
    },
    {
      id: 'hit-category',
      labelKey: 'market.template.method',
      search: (row) => row.category ?? '',
      compare: (a, b) => (a.category ?? '').localeCompare(b.category ?? ''),
      render: (row) => <span className="text-xs text-ink-soft">{row.category ?? notProvided}</span>,
    },
    {
      id: 'hit-language',
      labelKey: 'auth.session.language',
      compare: (a, b) => (a.language ?? '').localeCompare(b.language ?? ''),
      render: (row) => (
        <span className="num text-xs text-ink-soft">{row.language ?? notProvided}</span>
      ),
    },
    {
      id: 'hit-published',
      labelKey: 'common.live',
      compare: (a, b) => (a.publishedAt ?? '').localeCompare(b.publishedAt ?? ''),
      render: (row) => (
        <span className="num text-xs text-ink-soft">
          {formatTimestamp(row.publishedAt, locale, notProvided)}
        </span>
      ),
    },
  ];

  return (
    <div>
      <WorkspacePageHeader locale={locale} page={PAGE} />

      <section className="mt-6" aria-labelledby="workspace-documents">
        <h2 id="workspace-documents" className="field-label">
          {t('legal.title')}
        </h2>
        <div className="mt-3">
          {documents.ok ? (
            <WorkspaceDataGrid
              id="workspace-documents-caption"
              caption={t('statusPage.subtitle')}
              source={WORKSPACE_LEGAL_TEXTS_ENDPOINT}
              basePath={workspacePageHref(locale, PAGE.path)}
              searchParams={query}
              columns={documentColumns}
              rows={documentRows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <WorkspaceUnavailable
              source={WORKSPACE_LEGAL_TEXTS_ENDPOINT}
              status={documents.status}
              detail={documents.ok ? undefined : documents.error}
            />
          )}
        </div>
      </section>

      <section className="mt-6" aria-labelledby="workspace-search">
        <h2 id="workspace-search" className="field-label">
          {t('public.science.evidenceBase.evidenceCatalog')}
        </h2>
        <p className="num mt-2 break-words text-xs text-ink-faint">
          {WORKSPACE_CONTENT_SEARCH_ENDPOINT}
        </p>
        <div className="mt-3">
          {hits === null ? (
            <p className="card p-4 text-sm text-ink-soft">{t('learn.emptyDesc')}</p>
          ) : hits.ok ? (
            <WorkspaceDataGrid
              id="workspace-search-caption"
              caption={t('statusPage.subtitle')}
              source={WORKSPACE_CONTENT_SEARCH_ENDPOINT}
              basePath={workspacePageHref(locale, PAGE.path)}
              searchParams={query}
              columns={hitColumns}
              rows={hitRows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <WorkspaceUnavailable
              source={WORKSPACE_CONTENT_SEARCH_ENDPOINT}
              status={hits.status}
              detail={hits.ok ? undefined : hits.error}
            />
          )}
        </div>
      </section>

      <WorkspaceScopeNote page={PAGE} role={accessRole(access)} id="workspace-scope" />

      <WorkspaceCapabilityTable id="workspace-contract" capabilities={PAGE.capabilities} />

      <WorkspaceSourceNote
        source={`${WORKSPACE_LEGAL_TEXTS_ENDPOINT} · ${WORKSPACE_CONTENT_SEARCH_ENDPOINT}`}
        ok={documents.ok}
      />
    </div>
  );
}
