import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('auth');

  return {
    title: t('meta.title'),
    description: t('meta.description'),
    // Account pages are session-bound; they must never enter an index.
    robots: { index: false, follow: false },
  };
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return children;
}
