import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { apiGet } from '@/lib/api/client';
import {
  findCapability,
  isCapabilityWired,
  LIVE_LABEL_KEY,
  REAL_DATA_LABEL_KEY,
  STATE_LABEL_KEY,
  TELECOM_ROUTE,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type GatewayStatus = { status: string };
type VoiceHealth = { status: string; mode: string };

// Gateway contracts are read live; nothing about a telecom partner is assumed.
export const dynamic = 'force-dynamic';

const ussdCapability = findCapability(TELECOM_ROUTE, 'telecom-ussd-gateway');
const voiceCapability = findCapability(TELECOM_ROUTE, 'telecom-voice-gateway');
const voiceHealthCapability = findCapability(TELECOM_ROUTE, 'telecom-voice-health');

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t(TELECOM_ROUTE.headingKey),
    description: t('public.channels.lead'),
    alternates: {
      canonical: `${BASE_URL}/${locale}/telecom`,
    },
  };
}

export default async function TelecomPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const [ussd, voice, voiceHealth] = await Promise.all([
    apiGet<GatewayStatus>('/api/v1/ussd/status'),
    apiGet<GatewayStatus>('/api/v1/voice/status'),
    apiGet<VoiceHealth>('/api/v1/voice/health'),
  ]);

  const rows = [
    {
      id: 'telecom-ussd-gateway',
      label: t(ussdCapability?.labelKey ?? TELECOM_ROUTE.headingKey),
      endpoint: ussdCapability?.endpoint ?? null,
      state: ussd.ok ? ('ok' as const) : ('down' as const),
      detail: ussd.ok ? ussd.data.status : null,
    },
    {
      id: 'telecom-voice-gateway',
      label: t(voiceCapability?.labelKey ?? TELECOM_ROUTE.headingKey),
      endpoint: voiceCapability?.endpoint ?? null,
      state: voice.ok ? ('ok' as const) : ('down' as const),
      detail: voice.ok ? voice.data.status : null,
    },
    {
      id: 'telecom-voice-health',
      label: t(voiceHealthCapability?.labelKey ?? TELECOM_ROUTE.headingKey),
      endpoint: voiceHealthCapability?.endpoint ?? null,
      state: voiceHealth.ok ? ('ok' as const) : ('down' as const),
      detail: voiceHealth.ok ? voiceHealth.data.mode : null,
    },
    {
      id: 'telecom-sms-delivery',
      label: t('public.channels.sms'),
      endpoint: null,
      state: 'down' as const,
      detail: null,
    },
  ];

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <header>
        <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
          {t(TELECOM_ROUTE.headingKey)}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('public.channels.lead')}</p>
      </header>

      <section className="card mt-6 p-5" aria-labelledby="telecom-state">
        <h2 id="telecom-state" className="field-label">
          {t(STATE_LABEL_KEY)}
        </h2>
        <ul className="mt-3 space-y-2">
          {rows.map((row) => (
            <li key={row.id} className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-sm text-ink">{row.label}</span>
              <span className="flex flex-wrap items-center gap-3">
                <span className="num text-xs text-ink-faint">
                  {row.detail ?? row.endpoint ?? t(UNAVAILABLE_LABEL_KEY)}
                </span>
                <StatusDot
                  state={row.state}
                  label={row.state === 'ok' ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY)}
                />
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-4" aria-labelledby="telecom-capabilities">
        <h2 id="telecom-capabilities" className="field-label">
          {t('public.channels.channels')}
        </h2>
        <ul className="mt-3 space-y-2">
          {TELECOM_ROUTE.capabilities.map((capability) => (
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
                  state={isCapabilityWired(capability) ? 'warn' : 'down'}
                  label={
                    isCapabilityWired(capability) ? t('common.planned') : t(UNAVAILABLE_LABEL_KEY)
                  }
                />
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="card mt-4 p-5">
        <h2 className="field-label">{t('common.limits')}</h2>
        <ul className="mt-2 list-inside list-disc text-sm text-ink-soft">
          {t.raw('public.channels.limitsItems')?.map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <p className="mt-6 text-xs text-ink-soft">{t(REAL_DATA_LABEL_KEY)}</p>
    </div>
  );
}
