import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { apiGet } from '@/lib/api/client';
import {
  LIVE_LABEL_KEY,
  NEXT_DETAIL_KEY,
  NEXT_LABEL_KEY,
  REAL_DATA_LABEL_KEY,
  SERVICE_LABEL_KEY,
  SYSTEM_WEBGPU_FALLBACK_ROUTE,
  UNAVAILABLE_DETAIL_KEY,
  UNAVAILABLE_LABEL_KEY,
  UNAVAILABLE_TITLE_KEY,
} from '@/lib/domains/registry';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

// GPU capability is a client probe; the kernel state is read live per request.
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
    title: t(SYSTEM_WEBGPU_FALLBACK_ROUTE.headingKey),
    description: t('statusPage.subtitle'),
    // Internal operations surface: never indexed.
    robots: { index: false, follow: false },
    alternates: {
      canonical: `${BASE_URL}/${locale}/system/webgpu-fallback`,
    },
  };
}

export default async function WebGpuFallbackPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const kernels = await apiGet<{ available: boolean }>('/api/v1/models/cpp-status');
  const kernelsAvailable = kernels.ok && kernels.data.available;

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <header>
        <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
          {t(SYSTEM_WEBGPU_FALLBACK_ROUTE.headingKey)}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('statusPage.subtitle')}</p>
      </header>

      <section className="card mt-6 p-5" aria-labelledby="webgpu-fallback-state">
        <h2 id="webgpu-fallback-state" className="field-label">
          {t(SERVICE_LABEL_KEY)}
        </h2>
        <p className="mt-3 text-sm text-ink">{t(UNAVAILABLE_TITLE_KEY)}</p>
        <p className="mt-2 text-sm text-ink-soft">{t(UNAVAILABLE_DETAIL_KEY)}</p>
      </section>

      <section className="mt-4" aria-labelledby="webgpu-fallback-capabilities">
        <h2 id="webgpu-fallback-capabilities" className="field-label">
          {t('statusPage.state')}
        </h2>
        <ul className="mt-3 space-y-2">
          {SYSTEM_WEBGPU_FALLBACK_ROUTE.capabilities.map((capability) => {
            const available = capability.id === 'cpp-kernel-status' && kernelsAvailable;
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
                    state={available ? 'ok' : 'down'}
                    label={available ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY)}
                  />
                </span>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="card mt-4 p-5">
        <h2 className="field-label">{t(NEXT_LABEL_KEY)}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t(NEXT_DETAIL_KEY)}</p>
      </section>

      <p className="mt-6 text-xs text-ink-soft">{t(REAL_DATA_LABEL_KEY)}</p>
    </div>
  );
}
