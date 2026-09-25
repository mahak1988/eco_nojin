import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { SITE_URL as BASE_URL } from '@/config/site';
import { EndpointForm } from '../EndpointForm';

const CONTACT_PATH = '/api/v1/contact';

const TITLES: Record<string, string> = { fa: 'بازدید از مزرعه', en: 'Farm Visit' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'درخواست بازدید به گیتوی ارسال می‌شود؛ بازدیدی زمان‌بندی‌شده نمایش داده نمی‌شود',
  en: 'The visit request is posted to the gateway; no scheduled visit is shown',
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
      url: `${BASE_URL}/${locale}/public/visit`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/visit`,
      languages: {
        fa: `${BASE_URL}/fa/public/visit`,
        en: `${BASE_URL}/en/public/visit`,
      },
    },
  };
}

export default async function VisitPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.visit');
  const common = await getTranslations('common');
  const title = TITLES[locale] ?? TITLES.en;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source={CONTACT_PATH} label={title} verified={false} method={CONTACT_PATH}>
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('body')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{CONTACT_PATH}</h2>
        <Card density="cozy">
          <EndpointForm
            path={CONTACT_PATH}
            fields={[
              { name: 'name', label: common('total'), type: 'text', required: true },
              { name: 'email', label: 'email', type: 'email', required: true },
              { name: 'organization', label: common('view'), type: 'text', required: false },
              { name: 'message', label: common('error'), type: 'text', required: false },
            ]}
            submitLabel={t('scheduleVisit')}
            consentLabel={t('visitNote')}
          />
        </Card>
      </section>
    </main>
  );
}
