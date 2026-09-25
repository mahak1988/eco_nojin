import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';
import { SITE_URL as BASE_URL } from '@/config/site';
import { routing } from '@/i18n/routing';
import { apiGet, type CppStatus, type HydromaModel } from '@/lib/api/client';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('science');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/hydroma`,
      title: t('title'),
      description: t('lead'),
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/hydroma`,
      languages: Object.fromEntries(
        routing.locales.map((loc) => [loc, `${BASE_URL}/${loc}/hydroma`]),
      ),
    },
  };
}

export default async function HydromaPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const [cpp, models] = await Promise.all([
    apiGet<CppStatus>('/api/v1/models/cpp-status'),
    apiGet<HydromaModel[]>('/api/v1/hydroma/models'),
  ]);
  const available = cpp.ok && cpp.data.available;
  const kernels = cpp.ok ? cpp.data.kernels : [];
  const registered = models.ok ? models.data : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <h1 className="display text-4xl font-bold text-ink">{t('science.title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('science.lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-2">
        <div
          className={available ? 'card p-4 text-sm text-forest' : 'card p-4 text-sm text-copper'}
        >
          <strong>{available ? t('science.cppOk') : t('science.cppMissing')}</strong>
          <p className="mt-2 text-xs text-ink-soft">{t('science.modelsPublicNote')}</p>
          {kernels.length > 0 && (
            <p className="mt-2 text-xs text-ink-soft">
              {t('science.kernels')}: <span className="font-mono">{kernels.join(' · ')}</span>
            </p>
          )}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6 pb-16">
        <h2 className="text-sm font-semibold text-ink-soft">{t('science.modelsTitle')}</h2>
        {registered.length > 0 ? (
          <ul className="mt-3 divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
            {registered.map((model) => (
              <li
                key={model.id}
                className="flex flex-wrap items-baseline justify-between gap-4 px-4 py-3 text-sm"
              >
                <div className="min-w-0">
                  <span className="text-ink">{model.name}</span>
                  <p className="mt-1 text-xs text-ink-soft">{model.description}</p>
                </div>
                <span className="num shrink-0 text-xs text-ink-soft">
                  {model.category} · {model.version} · {model.language}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-xs text-ink-soft">
            {models.ok ? t('science.modelsEmpty') : t('statusLine.unavailable')}
          </p>
        )}
        <p className="mt-4 text-xs text-ink-soft">{t('science.modelsPublicNote')}</p>
      </section>
    </main>
  );
}
