import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

export const dynamic = 'force-dynamic';

export default async function OfflineToolsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');
  const offline = await getTranslations('offline');
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={template('source')}
          label={services('title')}
          verified={false}
          method={template('method')}
        >
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{offline('code')}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">{offline('title')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{offline('description')}</p>
          <p className="mt-3 text-xs text-ink-soft">
            {template('method')} · {t('unavailable')}
          </p>
        </Card>
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>

      <OwnerFooter />
    </main>
  );
}
