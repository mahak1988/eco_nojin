import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { WorkspaceUnavailablePage } from '@/components/workspace/WorkspaceUnavailablePage';
import { accessRole, authorizeWorkspace } from '@/lib/workspaces/guard';
import { getWorkspacePage } from '@/lib/workspaces/registry';

// No report contract is registered and no export may be offered, so the route
// reports its state only.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('reports');

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

export default async function ReportsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <WorkspaceUnavailablePage
      locale={locale}
      page={PAGE}
      role={accessRole(await authorizeWorkspace())}
      relatedPaths={['knowledge', 'operations/health', 'overview']}
      sourceNote="openapi.json"
    />
  );
}
