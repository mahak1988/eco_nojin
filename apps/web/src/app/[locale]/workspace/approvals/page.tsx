import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { WorkspaceUnavailablePage } from '@/components/workspace/WorkspaceUnavailablePage';
import { accessRole, authorizeWorkspace } from '@/lib/workspaces/guard';
import { getWorkspacePage } from '@/lib/workspaces/registry';

// The gateway registers no professional approval index, and the actions that do
// exist read personal data with no declared scope, so nothing is listed here.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('approvals');

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

export default async function ApprovalsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <WorkspaceUnavailablePage
      locale={locale}
      page={PAGE}
      role={accessRole(await authorizeWorkspace())}
      relatedPaths={['team', 'targets', 'overview']}
      sourceNote="openapi.json"
    />
  );
}
