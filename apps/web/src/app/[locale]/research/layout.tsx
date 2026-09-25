import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { RESEARCH_WORKSPACE_ROUTE } from '@/lib/domains/registry';

// The workspace is session-bound and reads live records per request.
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
    title: t(RESEARCH_WORKSPACE_ROUTE.headingKey),
    description: t('evidence.lead'),
    // Research records are not public; keep the workspace out of the index.
    robots: { index: false, follow: false },
  };
}

export default async function ResearchLayout({ children }: { children: React.ReactNode }) {
  return (
    <main id="main" className="mx-auto w-full max-w-6xl px-6 py-10">
      {children}
    </main>
  );
}
