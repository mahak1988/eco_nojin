import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { WorkspaceUnavailablePage } from '@/components/workspace/WorkspaceUnavailablePage';
import { accessRole, authorizeWorkspace } from '@/lib/workspaces/guard';
import { getWorkspacePage } from '@/lib/workspaces/registry';

// No case or dispute index is registered, so this route reports its state only.
export const dynamic = 'force-dynamic';

const PAGE = getWorkspacePage('cases');

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

export default async function CasesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <WorkspaceUnavailablePage
      locale={locale}
      page={PAGE}
      role={accessRole(await authorizeWorkspace())}
      relatedPaths={['assignments', 'knowledge', 'overview']}
      sourceNote="openapi.json"
    />
  );
}
