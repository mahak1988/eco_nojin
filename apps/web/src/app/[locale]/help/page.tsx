import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';
import { type RecoveryLinkItem, RecoveryLinks } from '@/components/system/RecoveryLinks';
import { RefreshStateButton } from '@/components/system/RefreshStateButton';
import { SupportDirectory, type SupportPersona } from '@/components/system/SupportDirectory';
import { type HealthRow, SystemHealthMatrix } from '@/components/system/SystemHealthMatrix';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import {
  ENDPOINT_LABEL_KEY,
  LIVE_LABEL_KEY,
  METRIC_LABEL_KEY,
  RESULT_LABEL_KEY,
  STATE_LABEL_KEY,
  UNAVAILABLE_LABEL_KEY,
} from '@/lib/domains/registry';

const PERSONAS_PATH = '/api/v1/support/personas';

const INTAKE_ENDPOINTS = [
  { id: 'contact', method: 'POST', path: '/api/v1/contact' },
  { id: 'support-chat', method: 'POST', path: '/api/v1/support/chat' },
] as const;

export const dynamic = 'force-dynamic';

function readPersonas(payload: unknown): SupportPersona[] {
  const personas = (payload as { personas?: unknown } | null)?.personas;
  if (!Array.isArray(personas)) return [];
  return personas.flatMap((entry) => {
    if (typeof entry !== 'object' || entry === null) return [];
    const { lang, name, role, intro, model } = entry as Record<string, unknown>;
    if (
      typeof lang !== 'string' ||
      typeof name !== 'string' ||
      typeof role !== 'string' ||
      typeof intro !== 'string' ||
      typeof model !== 'string'
    ) {
      return [];
    }
    return [{ lang, name, role, intro, model }];
  });
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('help.title'),
    description: t('help.lead'),
    alternates: {
      canonical: `${BASE_URL}/${locale}/help`,
      languages: {
        fa: `${BASE_URL}/fa/help`,
        en: `${BASE_URL}/en/help`,
      },
    },
  };
}

export default async function HelpPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const observedAt = new Date().toISOString();
  const personas = await apiGet<unknown>(PERSONAS_PATH);
  const directory = personas.ok ? readPersonas(personas.data) : [];

  const intakeRows: HealthRow[] = INTAKE_ENDPOINTS.map((endpoint) => ({
    id: endpoint.id,
    label: endpoint.path,
    token: endpoint.method,
    state: 'warn',
    stateLabel: t('common.planned'),
    result: null,
  }));

  const topics: RecoveryLinkItem[] = [
    {
      href: '/evidence',
      label: t('evidence.title'),
      detail: t('evidence.lead'),
      token: '/evidence',
    },
    {
      href: '/services',
      label: t('services.title'),
      detail: t('services.lead'),
      token: '/services',
    },
    {
      href: '/public/channels',
      label: t('public.channels.title'),
      detail: t('public.channels.lead'),
      token: '/public/channels',
    },
    { href: '/trust', label: t('trust.title'), detail: t('trust.lead'), token: '/trust' },
    {
      href: '/developers',
      label: t('developers.title'),
      detail: t('developers.lead'),
      token: '/developers',
    },
    { href: '/legal', label: t('legal.title'), detail: t('legal.lead'), token: '/legal' },
    {
      href: '/accessibility',
      label: t('accessibility.title'),
      detail: t('accessibility.lead'),
      token: '/accessibility',
    },
    {
      href: '/system',
      label: t('statusPage.service'),
      detail: t('statusPage.subtitle'),
      token: '/system',
    },
    {
      href: '/status',
      label: t('statusPage.title'),
      detail: t('statusPage.subtitle'),
      token: '/status',
    },
    { href: '/ai/feedback', label: t('ai.title'), detail: t('ai.lead'), token: '/ai/feedback' },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-5xl px-6 py-12">
        <header>
          <span className="chip num font-mono">help</span>
          <h1 className="display mt-3 text-3xl font-bold text-ink sm:text-4xl">
            {t('help.title')}
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('help.lead')}</p>
          <div className="mt-4 flex flex-wrap items-center gap-4">
            <span className="text-xs text-ink-faint">{t('help.lastObserved')}</span>
            <span className="num text-xs text-ink-faint">
              <time dateTime={observedAt}>{observedAt.slice(11, 19)}</time>
            </span>
            <RefreshStateButton label={t('common.retry')} />
          </div>
        </header>

        <div className="mt-6">
          <SupportDirectory
            personas={directory}
            heading={t('help.supportDirectoryTitle')}
            headingId="help-support"
            unavailable={t(UNAVAILABLE_LABEL_KEY)}
            endpoint={PERSONAS_PATH}
            endpointState={personas.ok ? t(LIVE_LABEL_KEY) : t(UNAVAILABLE_LABEL_KEY)}
          />
        </div>

        <section className="card mt-6 p-5" aria-labelledby="help-intake">
          <h2 id="help-intake" className="field-label">
            {t('help.intakeTitle')}
          </h2>
          <p className="mt-3 text-sm text-ink">{t('help.supportUnavailable')}</p>
          <p className="mt-2 text-sm text-ink-soft">{t('help.intakeLead')}</p>
          <div className="mt-4">
            <SystemHealthMatrix
              rows={intakeRows}
              labels={{
                metric: t(METRIC_LABEL_KEY),
                state: t(STATE_LABEL_KEY),
                result: t(RESULT_LABEL_KEY),
                caption: t(ENDPOINT_LABEL_KEY),
              }}
              emptyLabel={t(UNAVAILABLE_LABEL_KEY)}
            />
          </div>
        </section>

        <div className="mt-6">
          <RecoveryLinks
            links={topics}
            heading={t('help.topicsTitle')}
            headingId="help-topics"
            viewLabel={t('common.view')}
          />
        </div>
      </div>
    </main>
  );
}
