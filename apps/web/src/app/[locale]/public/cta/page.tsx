import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { EndpointForm } from '../EndpointForm';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const NEWSLETTER_PATH = '/api/v1/newsletter/subscribe';

const TITLES: Record<string, string> = { fa: 'شروع همکاری', en: 'Get Involved' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'مسیرهای موجود به‌صورت endpoint واقعی و فرم ارسال به گیتوی',
  en: 'Available paths as real endpoints and a form that posts to the gateway',
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
      url: `${BASE_URL}/${locale}/public/cta`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/cta`,
      languages: {
        fa: `${BASE_URL}/fa/public/cta`,
        en: `${BASE_URL}/en/public/cta`,
      },
    },
  };
}

export default async function CTAPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.cta');
  const common = await getTranslations('common');
  const title = TITLES[locale] ?? TITLES.en;

  const links = [
    { href: `/${locale}/public/audiences/farmers`, label: t('farmersLink') },
    { href: `/${locale}/public/audiences/government`, label: t('governmentLink') },
    { href: `/${locale}/public/audiences/investors`, label: t('investorsLink') },
    { href: `/${locale}/public/audiences/ngos`, label: t('ngosLink') },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={NEWSLETTER_PATH}
          label={title}
          verified={false}
          method={NEWSLETTER_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('body')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('optionsTitle')}</h2>
        <ul className="grid gap-2 sm:grid-cols-2">
          {links.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="block rounded-md border border-line px-4 py-3 text-sm font-semibold text-[var(--color-forest)]"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{NEWSLETTER_PATH}</h2>
        <Card density="cozy">
          <p className="mb-4 text-sm text-ink-soft">{t('newsletterBody')}</p>
          <EndpointForm
            path={NEWSLETTER_PATH}
            fields={[
              { name: 'email', label: 'email', type: 'email', required: true },
              { name: 'name', label: common('total'), type: 'text', required: false },
            ]}
            submitLabel={t('newsletterSubmit')}
            consentLabel={t('newsletterConsent')}
          />
        </Card>
      </section>
    </main>
  );
}
