import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { UnavailableCapability } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

// No workshop or event calendar is served by the registered gateway routes.
const MISSING_PATH = '/api/v1/public/education/workshops';
const SEARCH_PATH = '/api/v1/content/search';

const TITLES: Record<string, string> = { fa: 'کارگاه‌های حضوری', en: 'Workshops' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'تقویم کارگاه در گیتوی ثبت نشده است؛ هیچ تاریخ یا ظرفیتی نمایش داده نمی‌شود',
  en: 'No workshop calendar is registered on the gateway; no date or capacity is shown',
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: TITLES[locale] ?? TITLES.en,
    description: DESCRIPTIONS[locale] ?? DESCRIPTIONS.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/education/workshops`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/education/workshops`,
      languages: {
        fa: `${BASE_URL}/fa/public/education/workshops`,
        en: `${BASE_URL}/en/public/education/workshops`,
      },
    },
  };
}

export default async function WorkshopsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const learn = await getTranslations('learn');
  const common = await getTranslations('common');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source={MISSING_PATH} label={title} verified={false} method={MISSING_PATH}>
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <UnavailableCapability path={MISSING_PATH} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{SEARCH_PATH}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">{learn('emptyTitle')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{learn('emptyDesc')}</p>
          <Link
            href={`/${locale}/public/education/library`}
            className="mt-3 inline-flex text-sm font-semibold text-[var(--color-forest)]"
          >
            {common('view')}
          </Link>
        </Card>
      </section>
    </main>
  );
}
