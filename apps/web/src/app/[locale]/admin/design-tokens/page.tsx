import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminDataGrid, type AdminGridColumn } from '@/components/admin/AdminDataGrid';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import {
  AdminCapabilityTable,
  AdminSourceNote,
  AdminUnavailable,
} from '@/components/admin/AdminStates';
import {
  type AdminCssStateRow,
  type AdminCssVariableRow,
  type AdminTokenRow,
  GLOBALS_CSS_PATH,
  readCssStates,
  readCssVariables,
  readDesignTokens,
  TOKENS_CSS_PATH,
  TOKENS_JSON_PATH,
} from '@/components/admin/admin-local-data';
import { getAdminSection } from '@/components/admin/admin-sections';
import { StatusDot } from '@/components/StatusDot';

// The token inventory is read from the real token files on every request.
export const dynamic = 'force-dynamic';

const section = getAdminSection('design-tokens');

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('accessibility.title'),
    description: t('accessibility.lead'),
    robots: { index: false, follow: false },
  };
}

const tokenColumns: readonly AdminGridColumn<AdminTokenRow>[] = [
  {
    id: 'token',
    labelKey: 'statusPage.label',
    search: (row) => `${row.id} ${row.value} ${row.description}`,
    compare: (a, b) => a.id.localeCompare(b.id),
    render: (row) => (
      <span className="block">
        <span className="num block break-all font-medium text-ink">{row.id}</span>
        <span className="block break-words text-xs text-ink-soft">{row.value}</span>
      </span>
    ),
  },
  {
    id: 'group',
    labelKey: 'market.bazaar.type',
    search: (row) => row.group,
    compare: (a, b) => a.group.localeCompare(b.group),
    render: (row) => <span className="text-xs">{row.group}</span>,
  },
  {
    id: 'type',
    labelKey: 'market.template.method',
    search: (row) => row.type,
    compare: (a, b) => a.type.localeCompare(b.type),
    render: (row) => <span className="num text-xs">{row.type || '—'}</span>,
  },
  {
    id: 'description',
    labelKey: 'common.limits',
    search: (row) => row.description,
    compare: (a, b) => a.description.localeCompare(b.description),
    render: (row) => <span className="block break-words text-xs">{row.description || '—'}</span>,
  },
];

const variableColumns: readonly AdminGridColumn<AdminCssVariableRow>[] = [
  {
    id: 'token',
    labelKey: 'statusPage.label',
    search: (row) => `${row.token} ${row.value} ${row.file}`,
    compare: (a, b) => a.token.localeCompare(b.token),
    render: (row) => (
      <span className="block">
        <span className="num block break-all font-medium text-ink">{row.token}</span>
        <span className="num block break-words text-xs text-ink-soft">{row.value}</span>
      </span>
    ),
  },
  {
    id: 'file',
    labelKey: 'market.template.source',
    search: (row) => row.file,
    compare: (a, b) => a.file.localeCompare(b.file),
    render: (row) => <span className="num text-xs text-ink-soft">{row.file}</span>,
  },
];

const stateColumns: readonly AdminGridColumn<AdminCssStateRow>[] = [
  {
    id: 'selector',
    labelKey: 'statusPage.state',
    search: (row) => row.selector,
    compare: (a, b) => a.selector.localeCompare(b.selector),
    render: (row) => <span className="num block break-all text-xs text-ink">{row.selector}</span>,
  },
  {
    id: 'file',
    labelKey: 'market.template.source',
    search: (row) => row.file,
    compare: (a, b) => a.file.localeCompare(b.file),
    render: (row) => <span className="num text-xs text-ink-soft">{row.file}</span>,
  },
];

export default async function DesignTokensPage({
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

  const [tokens, variables, globals, states] = await Promise.all([
    readDesignTokens(),
    readCssVariables(TOKENS_CSS_PATH),
    readCssVariables(GLOBALS_CSS_PATH),
    readCssStates(GLOBALS_CSS_PATH),
  ]);

  const variableRows: AdminCssVariableRow[] = [
    ...(variables.ok ? variables.data : []),
    ...(globals.ok ? globals.data : []),
  ];
  const stateRows: AdminCssStateRow[] = states.ok ? states.data : [];
  const filesOk = tokens.ok && variables.ok && globals.ok && states.ok;

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <div className="card mt-6 p-4">
        <dl className="grid gap-3 sm:grid-cols-3">
          <div>
            <dt className="field-label">{TOKENS_JSON_PATH}</dt>
            <dd className="num mt-1 text-sm text-ink">
              {tokens.ok ? new Intl.NumberFormat(locale).format(tokens.data.length) : '—'}
            </dd>
          </div>
          <div>
            <dt className="field-label">{TOKENS_CSS_PATH}</dt>
            <dd className="num mt-1 text-sm text-ink">
              {variables.ok ? new Intl.NumberFormat(locale).format(variables.data.length) : '—'}
            </dd>
          </div>
          <div>
            <dt className="field-label">{GLOBALS_CSS_PATH}</dt>
            <dd className="num mt-1 text-sm text-ink">
              {globals.ok ? new Intl.NumberFormat(locale).format(globals.data.length) : '—'}
            </dd>
          </div>
        </dl>
        <p className="mt-3 text-xs text-ink-soft">
          <StatusDot
            state={filesOk ? 'ok' : 'down'}
            label={filesOk ? t('statusLine.realData') : t('statusLine.unavailable')}
          />
        </p>
      </div>

      <section className="mt-6" aria-labelledby="admin-tokens-dtcg">
        <h2 id="admin-tokens-dtcg" className="field-label">
          {t('statusPage.label')}
        </h2>
        <div className="mt-3">
          {tokens.ok ? (
            <AdminDataGrid
              id="admin-tokens-caption"
              caption={`${TOKENS_JSON_PATH} · W3C DTCG`}
              source={TOKENS_JSON_PATH}
              basePath={`/${locale}/admin/design-tokens`}
              searchParams={query}
              columns={tokenColumns}
              rows={tokens.data}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <AdminUnavailable
              source={TOKENS_JSON_PATH}
              status={tokens.status}
              detail={tokens.error}
            />
          )}
        </div>
      </section>

      <section className="mt-6" aria-labelledby="admin-tokens-variables">
        <h2 id="admin-tokens-variables" className="field-label">
          {t('market.template.source')}
        </h2>
        <div className="mt-3">
          {variableRows.length > 0 ? (
            <AdminDataGrid
              id="admin-variables-caption"
              caption={`${TOKENS_CSS_PATH} · ${GLOBALS_CSS_PATH}`}
              source={`${TOKENS_CSS_PATH} · ${GLOBALS_CSS_PATH}`}
              basePath={`/${locale}/admin/design-tokens`}
              searchParams={query}
              columns={variableColumns}
              rows={variableRows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <AdminUnavailable
              source={`${TOKENS_CSS_PATH} · ${GLOBALS_CSS_PATH}`}
              detail={variables.ok ? undefined : variables.error}
            />
          )}
        </div>
      </section>

      <section className="mt-6" aria-labelledby="admin-tokens-states">
        <h2 id="admin-tokens-states" className="field-label">
          {t('statusPage.state')}
        </h2>
        <div className="mt-3">
          {stateRows.length > 0 ? (
            <AdminDataGrid
              id="admin-states-caption"
              caption={GLOBALS_CSS_PATH}
              source={GLOBALS_CSS_PATH}
              basePath={`/${locale}/admin/design-tokens`}
              searchParams={query}
              columns={stateColumns}
              rows={stateRows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <AdminUnavailable source={GLOBALS_CSS_PATH} detail={t('statusLine.noData')} />
          )}
        </div>
      </section>

      <AdminCapabilityTable id="admin-tokens-contract" capabilities={section.capabilities} />

      <AdminSourceNote
        source={`${TOKENS_JSON_PATH} · ${TOKENS_CSS_PATH} · ${GLOBALS_CSS_PATH}`}
        ok={filesOk}
      />
    </div>
  );
}
