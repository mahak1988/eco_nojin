import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { UnavailableCapability } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const SLUGS_PATH = '/api/v1/legal-texts/slugs';
const TEXT_PATH = '/api/v1/legal-texts/{locale}/governance';

const TITLES: Record<string, string> = {
  fa: 'سازماندهی حکمرانی',
  en: 'Governance Structure',
};
const DESCRIPTIONS: Record<string, string> = {
  fa: 'سگیرکد حکمرانی در سرویس متن‌های حقوقی ثبت نشده است؛ هیچ بدنه یا ساختاری نمایش داده نمی‌شود',
  en: 'No governance slug is registered in legal-texts, so no body or structure is shown',
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
      url: `${BASE_URL}/${locale}/public/policy/governance`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/policy/governance`,
      languages: {
        fa: `${BASE_URL}/fa/public/policy/governance`,
        en: `${BASE_URL}/en/public/policy/governance`,
      },
    },
  };
}

export default async function GovernancePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const common = await getTranslations('common');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;
  const missing = TEXT_PATH.replace('{locale}', locale).replace('{slug}', 'governance');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <ProvenanceStamp source={missing} label={title} verified={false} method={missing}>
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
        <div className="mt-6">
          <UnavailableCapability path={missing} />
        </div>
        <p className="mt-6 text-xs text-ink-soft">
          {common('limits')} · {SLUGS_PATH}
        </p>
      </div>
    </main>
  );
}
