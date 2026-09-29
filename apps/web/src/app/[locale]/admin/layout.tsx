import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminShell } from '@/components/admin/AdminShell';
import { hasRole } from '@/lib/auth/roles';
import {
  ADMIN_CONSOLE_ROLES,
  ADMIN_CONSOLE_ROUTE,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';
import { type SessionRecord, sessionCookieName } from '@/lib/session/session-cookie';
import { getStoredSession } from '@/lib/session/store';

// Authorization is resolved per request on the server.
export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t(ADMIN_CONSOLE_ROUTE.headingKey),
    description: t('statusPage.subtitle'),
    // A role-gated console must never enter an index.
    robots: { index: false, follow: false },
  };
}

/**
 * Deny by default: any failure to resolve the session — missing cookie,
 * expired record, unreachable store — is treated as "not authorized".
 */
async function readConsoleSession(): Promise<SessionRecord | null> {
  try {
    const store = await cookies();
    const id = store.get(sessionCookieName())?.value;
    return id ? await getStoredSession(id) : null;
  } catch {
    return null;
  }
}

export default async function AdminLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const session = await readConsoleSession();
  const authorized = session !== null && hasRole(session.user.role, ADMIN_CONSOLE_ROLES);

  if (!authorized) {
    return (
      <main id="main" className="mx-auto min-h-[60vh] max-w-2xl px-6 py-12">
        <h1 className="display text-3xl font-bold text-ink">{t(ADMIN_CONSOLE_ROUTE.headingKey)}</h1>
        <p className="mt-3 text-sm text-ink-soft">{t('auth.errors.forbidden')}</p>
        <p className="num mt-2 text-xs text-ink-faint">{t(UNAVAILABLE_LABEL_KEY)}</p>
        <Link href={`/${locale}/auth/login`} className="btn btn-ghost mt-6">
          {t('auth.common.signIn')}
        </Link>
      </main>
    );
  }

  return (
    <main id="main" className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <AdminShell>{children}</AdminShell>
    </main>
  );
}
