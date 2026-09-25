import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const LEGAL_TEXTS_PATH = '/api/v1/legal-texts/{locale}/{slug}';

const TITLES: Record<string, string> = { fa: 'مجوزهای متن‌باز', en: 'Open Source Licenses' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'سرویس متن‌های حقوقی سگیرکد «licensing» را ثبت نکرده است؛ بنابراین فهرست مجوزی نمایش داده نمی‌شود.',
  en: 'The legal-texts service registers no “licensing” slug, so no license inventory is shown.',
};

const NOTES: Record<string, string> = {
  fa: 'سرویس متن‌های حقوقی فقط سگیرکدهای ثبت‌شده را می‌پذیرد و سگیرکدی با نام licensing در آن ثبت نشده است.',
  en: 'The legal-texts service only accepts registered slugs, and no licensing slug is registered.',
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
      url: `${BASE_URL}/${locale}/public/policy/licensing`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/policy/licensing`,
      languages: {
        fa: `${BASE_URL}/fa/public/policy/licensing`,
        en: `${BASE_URL}/en/public/policy/licensing`,
      },
    },
  };
}

export default async function LicensingPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <ProvenanceStamp
          source={template('source')}
          label={title}
          verified={false}
          method={LEGAL_TEXTS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{DESCRIPTIONS[locale] ?? DESCRIPTIONS.en}</p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <StatusDot state="down" label={status('unavailable')} />
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-semibold text-ink">{template('unavailableTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{NOTES[locale] ?? NOTES.en}</p>
          <p className="mt-3 text-xs text-ink-soft">{LEGAL_TEXTS_PATH}</p>
        </Card>
      </div>
    </main>
  );
}
