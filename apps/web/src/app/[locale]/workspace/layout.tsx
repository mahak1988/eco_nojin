import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { WorkspaceShell } from '@/components/workspace/WorkspaceShell';
import {
  readWorkspaceSession,
  resolveWorkspaceAccess,
  workspaceNavigationFor,
} from '@/lib/workspaces/guard';
import { getWorkspacePage } from '@/lib/workspaces/registry';

// Authorization is resolved per request on the server; nothing is cached.
export const dynamic = 'force-dynamic';

const OVERVIEW = getWorkspacePage('overview');

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t(OVERVIEW.labelKey),
    description: t(OVERVIEW.leadKey),
    // Professional work is never public: keep the surface out of the index.
    robots: { index: false, follow: false },
  };
}

export default async function WorkspaceLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  // One deny-by-default decision for the whole surface. A missing cookie, an
  // expired record, an unreachable store, an inactive account or a role outside
  // the allowlist all resolve to the same refusal, and no child page may weaken
  // it: pages report on this gate, they never re-implement it.
  const access = resolveWorkspaceAccess(await readWorkspaceSession());

  if (access.status === 'denied') {
    return (
      <main id="main" className="mx-auto min-h-[60vh] max-w-2xl px-6 py-12">
        <p className="num chip">/{locale}/workspace</p>
        <h1 className="display mt-4 text-3xl font-bold text-ink">{t(OVERVIEW.labelKey)}</h1>
        <p className="mt-3 text-sm text-ink-soft">{t('auth.errors.forbidden')}</p>
        <p className="num mt-2 text-xs text-ink-faint">{t('statusLine.unavailable')}</p>
        <p className="mt-2 text-xs text-ink-soft">{t('auth.session.lead')}</p>
        <Link href={`/${locale}/auth/login`} className="btn btn-ghost mt-6">
          {t('auth.common.signIn')}
        </Link>
      </main>
    );
  }

  return (
    <main id="main" className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <WorkspaceShell groups={workspaceNavigationFor(access)} sessionRole={access.role}>
        {children}
      </WorkspaceShell>
    </main>
  );
}
