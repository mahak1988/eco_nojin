import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { apiGet } from '@/lib/api/client';
import {
  isUssdMenuLanguage,
  LIVE_LABEL_KEY,
  REAL_DATA_LABEL_KEY,
  SIMPLE_ACCESS_ROUTE,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type MenuPreview = { language: string; menu_text: string };
type GatewayStatus = { status: string };

// Channel state is read from the gateway on every request.
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
    title: t(SIMPLE_ACCESS_ROUTE.headingKey),
    description: t('public.channels.lead'),
    alternates: {
      canonical: `${BASE_URL}/${locale}/simple`,
    },
  };
}

export default async function SimpleAccessPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  // The USSD menu endpoint only serves en/fa/ar; other locales get the honest
  // unavailable state instead of an unrelated language.
  const menuLanguage = isUssdMenuLanguage(locale) ? locale : null;
  const [menu, gateway] = await Promise.all([
    menuLanguage
      ? apiGet<MenuPreview>(`/api/v1/ussd/menu/preview?language=${menuLanguage}`)
      : Promise.resolve({ ok: false as const, error: 'language not served', status: 0 }),
    apiGet<GatewayStatus>('/api/v1/ussd/status'),
  ]);

  const menuText = menu.ok ? menu.data.menu_text : null;

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <header>
        <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
          {t(SIMPLE_ACCESS_ROUTE.headingKey)}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('public.channels.lead')}</p>
      </header>

      <section className="card mt-6 p-5" aria-labelledby="simple-menu">
        <h2 id="simple-menu" className="field-label">
          {t('public.channels.ussd')}
        </h2>
        {menuText ? (
          <p className="num mt-3 text-sm text-ink" dir="auto">
            {menuText}
          </p>
        ) : (
          <div className="mt-3 space-y-2">
            <p className="text-sm text-ink">{t(UNAVAILABLE_LABEL_KEY)}</p>
            <p className="text-sm text-ink-soft">{t('public.channels.whatDesc')}</p>
          </div>
        )}
      </section>

      <section className="mt-4" aria-labelledby="simple-channels">
        <h2 id="simple-channels" className="field-label">
          {t('public.channels.channels')}
        </h2>
        <ul className="mt-3 space-y-2">
          {SIMPLE_ACCESS_ROUTE.capabilities.map((capability) => {
            const live =
              capability.id === 'simple-ussd-menu'
                ? menu.ok
                : capability.id === 'simple-ussd-gateway' && gateway.ok;
            return (
              <li
                key={capability.id}
                className="card flex flex-wrap items-center justify-between gap-3 p-4"
              >
                <span className="text-sm text-ink">{t(capability.labelKey)}</span>
                <span className="flex flex-wrap items-center gap-3">
                  <span className="num text-xs text-ink-faint">
                    {capability.endpoint ?? t(UNAVAILABLE_LABEL_KEY)}
                  </span>
                  <StatusDot
                    state={live ? 'ok' : 'down'}
                    label={live ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY)}
                  />
                </span>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="mt-4 grid gap-4 md:grid-cols-3">
        <div className="card p-5">
          <h2 className="field-label">{t('common.evidence')}</h2>
          <ul className="mt-2 list-inside list-disc text-sm text-ink-soft">
            {t.raw('public.channels.evidenceItems')?.map((item: string) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="card p-5">
          <h2 className="field-label">{t('common.limits')}</h2>
          <ul className="mt-2 list-inside list-disc text-sm text-ink-soft">
            {t.raw('public.channels.limitsItems')?.map((item: string) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="card p-5">
          <h2 className="field-label">{t('common.next')}</h2>
          <ul className="mt-2 list-inside list-disc text-sm text-ink-soft">
            {t.raw('public.channels.nextItems')?.map((item: string) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <p className="mt-6 text-xs text-ink-soft">{t(REAL_DATA_LABEL_KEY)}</p>
    </div>
  );
}
