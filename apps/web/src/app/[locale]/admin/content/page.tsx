import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminDataGrid, type AdminGridColumn } from '@/components/admin/AdminDataGrid';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import {
  AdminCapabilityTable,
  AdminRoleGate,
  AdminSourceNote,
  AdminUnavailable,
} from '@/components/admin/AdminStates';
import { getAdminSection } from '@/components/admin/admin-sections';
import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { StatusDot } from '@/components/StatusDot';
import { hasRole } from '@/lib/auth/roles';

// The content index is read from the live gateway on every request.
export const dynamic = 'force-dynamic';

const section = getAdminSection('content');
const ENDPOINT = section.capabilities.find((item) => item.id === 'content-index')?.endpoint ?? '';

type ContentRow = {
  id: string;
  title: string;
  category: string;
  language: string;
  status: string;
  updated_at: string;
  published_at: string | null;
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('statements.title'),
    description: t('statusPage.subtitle'),
    robots: { index: false, follow: false },
  };
}

function text(value: string | null | undefined): string {
  return typeof value === 'string' ? value : '';
}

export default async function ContentPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  await params;
  const query = await searchParams;
  setRequestLocale(locale);
  const t = await getTranslations();

  const session = await readAdminSession();
  const sessionRole = session?.user.role ?? 'regular';
  const allowed = hasRole(sessionRole, section.roles);

  const content =
    allowed && ENDPOINT !== '' ? await adminGet<ContentRow[]>(adminToken(session), ENDPOINT) : null;
  const rows: ContentRow[] = content?.ok && Array.isArray(content.data) ? content.data : [];

  const columns: readonly AdminGridColumn<ContentRow>[] = [
    {
      id: 'title',
      labelKey: 'statements.title',
      search: (row) => row.title,
      compare: (a, b) => a.title.localeCompare(b.title),
      render: (row) => (
        <span className="block">
          <span className="block break-words font-medium text-ink">{row.title}</span>
          <span className="num block text-[0.65rem] text-ink-faint">{`#${row.id}`}</span>
        </span>
      ),
    },
    {
      id: 'status',
      labelKey: 'statusPage.state',
      search: (row) => text(row.status),
      compare: (a, b) => text(a.status).localeCompare(text(b.status)),
      render: (row) => (
        <StatusDot
          state={row.status === 'published' ? 'ok' : 'warn'}
          label={text(row.status) || t('statusLine.unavailable')}
        />
      ),
    },
    {
      id: 'category',
      labelKey: 'market.bazaar.type',
      search: (row) => text(row.category),
      compare: (a, b) => text(a.category).localeCompare(text(b.category)),
      render: (row) => <span className="text-xs">{text(row.category) || '—'}</span>,
    },
    {
      id: 'language',
      labelKey: 'auth.session.language',
      search: (row) => text(row.language),
      compare: (a, b) => text(a.language).localeCompare(text(b.language)),
      render: (row) => <span className="num text-xs">{text(row.language) || '—'}</span>,
    },
    {
      id: 'published',
      labelKey: 'common.released',
      search: (row) => text(row.published_at),
      compare: (a, b) => text(a.published_at).localeCompare(text(b.published_at)),
      render: (row) => <span className="num text-xs">{text(row.published_at) || '—'}</span>,
    },
  ];

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <AdminRoleGate id="admin-content-roles" required={section.roles} sessionRole={sessionRole} />

      <section className="mt-6" aria-labelledby="admin-content-index">
        <h2 id="admin-content-index" className="field-label">
          {t('common.total')}
        </h2>
        <div className="mt-3">
          {content === null ? (
            <AdminUnavailable source={ENDPOINT} status={allowed ? 403 : 401} />
          ) : content.ok ? (
            <AdminDataGrid
              id="admin-content-caption"
              caption={t('statusPage.subtitle')}
              source={ENDPOINT}
              basePath={`/${locale}/admin/content`}
              searchParams={query}
              columns={columns}
              rows={rows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <AdminUnavailable source={ENDPOINT} status={content.status} detail={content.error} />
          )}
        </div>
      </section>

      <AdminCapabilityTable id="admin-content-contract" capabilities={section.capabilities} />

      <AdminSourceNote source={ENDPOINT} ok={content?.ok ?? false} />
    </div>
  );
}
