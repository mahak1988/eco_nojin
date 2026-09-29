import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { EndpointForm } from '../EndpointForm';

const CONTACT_PATH = '/api/v1/contact';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-visit');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/visit`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/visit'),
      languages: languageAlternates('/public/visit'),
    },
  };
}

export default async function VisitPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-visit');
  const t = await getTranslations('public.visit');
  const common = await getTranslations('common');
  const title = meta('title');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp
            source={CONTACT_PATH}
            label={title}
            verified={false}
            method={CONTACT_PATH}
          />
        </div>
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
