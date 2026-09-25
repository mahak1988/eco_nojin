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

// The user index is read from the live gateway on every request.
export const dynamic = 'force-dynamic';

const section = getAdminSection('users');
const ENDPOINT = section.capabilities.find((item) => item.id === 'users-index')?.endpoint ?? '';

type AdminUserRow = {
  id: string;
  email: string;
  full_name: string | null;
  role: string | null;
  country: string | null;
  language: string | null;
  is_active: boolean;
  is_email_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
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
    title: t('statusLine.beneficiaries'),
    description: t('statusPage.subtitle'),
    robots: { index: false, follow: false },
  };
}

function text(value: string | null | undefined): string {
  return typeof value === 'string' ? value : '';
}

export default async function UsersPage({
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

  const session = await readAdminSession();
  const sessionRole = session?.user.role ?? 'regular';
  const allowed = hasRole(sessionRole, section.roles);

  const users =
    allowed && ENDPOINT !== ''
      ? await adminGet<AdminUserRow[]>(adminToken(session), ENDPOINT)
      : null;
  const rows: AdminUserRow[] = users?.ok && Array.isArray(users.data) ? users.data : [];

  const columns: readonly AdminGridColumn<AdminUserRow>[] = [
    {
      id: 'email',
      labelKey: 'auth.common.email',
      search: (row) => `${row.email} ${text(row.full_name)}`,
      compare: (a, b) => a.email.localeCompare(b.email),
      render: (row) => (
        <span className="block">
          <span className="block break-all font-medium text-ink">{row.email}</span>
          <span className="block break-words text-xs text-ink-soft">
            {text(row.full_name) || t('auth.session.unknown')}
          </span>
        </span>
      ),
    },
    {
      id: 'role',
      labelKey: 'auth.session.role',
      search: (row) => text(row.role),
      compare: (a, b) => text(a.role).localeCompare(text(b.role)),
      render: (row) => <span className="num text-xs">{text(row.role) || '—'}</span>,
    },
    {
      id: 'language',
      labelKey: 'auth.session.language',
      search: (row) => text(row.language),
      compare: (a, b) => text(a.language).localeCompare(text(b.language)),
      render: (row) => <span className="num text-xs">{text(row.language) || '—'}</span>,
    },
    {
      id: 'country',
      labelKey: 'auth.session.country',
      search: (row) => text(row.country),
      compare: (a, b) => text(a.country).localeCompare(text(b.country)),
      render: (row) => <span className="text-xs">{text(row.country) || '—'}</span>,
    },
    {
      id: 'active',
      labelKey: 'auth.session.accountActive',
      search: (row) => String(row.is_active),
      compare: (a, b) => Number(a.is_active) - Number(b.is_active),
      render: (row) => (
        <StatusDot
          state={row.is_active ? 'ok' : 'down'}
          label={
            row.is_active ? t('auth.session.accountActive') : t('auth.session.accountInactive')
          }
        />
      ),
    },
    {
      id: 'verified',
      labelKey: 'auth.session.emailVerified',
      search: (row) => String(row.is_email_verified),
      compare: (a, b) => Number(a.is_email_verified) - Number(b.is_email_verified),
      render: (row) => (
        <StatusDot
          state={row.is_email_verified ? 'ok' : 'warn'}
          label={
            row.is_email_verified
              ? t('auth.session.emailVerified')
              : t('auth.session.emailNotVerified')
          }
        />
      ),
    },
    {
      id: 'created',
      labelKey: 'auth.session.memberSince',
      search: (row) => row.created_at,
      compare: (a, b) => a.created_at.localeCompare(b.created_at),
      render: (row) => <span className="num text-xs">{row.created_at || '—'}</span>,
    },
  ];

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <AdminRoleGate id="admin-users-roles" required={section.roles} sessionRole={sessionRole} />

      <section className="mt-6" aria-labelledby="admin-users-index">
        <h2 id="admin-users-index" className="field-label">
          {t('common.total')}
        </h2>
        <div className="mt-3">
          {users === null ? (
            <AdminUnavailable source={ENDPOINT} status={allowed ? 403 : 401} />
          ) : users.ok ? (
            <AdminDataGrid
              id="admin-users-caption"
              caption={t('statusPage.subtitle')}
              source={ENDPOINT}
              basePath={`/${locale}/admin/users`}
              searchParams={query}
              columns={columns}
              rows={rows}
              rowId={(row) => row.id}
              emptyMessage={t('statusLine.noData')}
            />
          ) : (
            <AdminUnavailable source={ENDPOINT} status={users.status} detail={users.error} />
          )}
        </div>
      </section>

      <AdminCapabilityTable id="admin-users-contract" capabilities={section.capabilities} />

      <AdminSourceNote source={ENDPOINT} ok={users?.ok ?? false} />
    </div>
  );
}
