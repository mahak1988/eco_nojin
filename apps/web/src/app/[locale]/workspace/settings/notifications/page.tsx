import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { WorkspaceUnavailablePage } from '@/components/workspace/WorkspaceUnavailablePage';
import { accessRole, authorizeWorkspace } from '@/lib/workspaces/guard';
import { getWorkspacePage } from '@/lib/workspaces/registry';

// The notification route answers with a fixed payload and its update route
// persists nothing, so no preference may be shown as saved.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('settings-notifications');

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

export default async function SettingsNotificationsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <WorkspaceUnavailablePage
      locale={locale}
      page={PAGE}
      role={accessRole(await authorizeWorkspace())}
      relatedPaths={['settings', 'settings/access']}
      sourceNote="/api/v1/auth/notifications"
    />
  );
}
