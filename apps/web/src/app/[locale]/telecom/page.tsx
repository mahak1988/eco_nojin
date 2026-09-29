import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { StateSlot } from '@/components/ui/StateSlot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { isUssdMenuLanguage } from '@/lib/domains/registry';
import { MessageEditor } from './MessageEditor';

export const dynamic = 'force-dynamic';

/**
 * The five reads behind the telecom hub. All five are published GETs; none of
 * them is a delivery status, because the gateway does not publish one and
 * `ussd.py:103` says so in its own note.
 */
const READS = [
  { id: 'ussd-status', path: '/api/v1/ussd/status' },
  { id: 'ussd-health', path: '/api/v1/ussd/health' },
  { id: 'voice-status', path: '/api/v1/voice/status' },
  { id: 'voice-health', path: '/api/v1/voice/health' },
  { id: 'voice-languages', path: '/api/v1/voice/languages' },
] as const;

/** `endpoint: null` in the registry, because no delivery contract exists. */
const SMS_DELIVERY = '/api/v1/ussd/sms';

type MenuPreview = { language: string; menu_text: string };

type Languages = { languages?: string[]; supported?: string[] };

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.telecom');

  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/telecom`,
      title: t('metaTitle'),
      description: t('metaDescription'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/telecom'),
      languages: languageAlternates('/telecom'),
    },
  };
}

/** Flattens whatever the voice gateway calls its language list. */
function languagesOf(data: Languages): string[] {
  const direct = data.languages ?? data.supported ?? [];
  return Array.isArray(direct)
    ? direct.filter((entry): entry is string => typeof entry === 'string')
    : [];
}

export default async function TelecomPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.telecom');
  const channels = await getTranslations('public.channels');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');

  // The USSD menu endpoint serves en/fa/ar only. Other locales are told so
  // rather than shown a menu in a language nobody asked for.
  const menuLanguage = isUssdMenuLanguage(locale) ? locale : null;

  const [reads, menu] = await Promise.all([
    Promise.all(READS.map((read) => apiGet<Record<string, unknown>>(read.path))),
    menuLanguage
      ? apiGet<MenuPreview>(`/api/v1/ussd/menu/preview?language=${menuLanguage}`)
      : Promise.resolve({
          ok: false as const,
          status: 0,
          error: `language=${locale} not served`,
        }),
  ]);

  const answered = reads.filter((result) => result.ok).length;
  const state = (() => {
    if (answered === READS.length) return 'ready' as const;
    if (answered === 0) {
      return reads.every((result) => !result.ok && result.status === 0)
        ? ('offline' as const)
        : ('error' as const);
    }
    return 'partial' as const;
  })();

  const languagesResult = reads.find((_, index) => READS[index].id === 'voice-languages');
  const languages = languagesResult?.ok ? languagesOf(languagesResult.data as Languages) : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-16 pt-8">
        <header>
          <h1 className="display text-3xl font-bold text-balance text-ink sm:text-4xl">
            {t('metaTitle')}
          </h1>
          <p className="mt-3 max-w-2xl text-sm text-ink-soft">{t('metaDescription')}</p>
        </header>

        <section className="mt-8" aria-labelledby="telecom-state">
          <h2 id="telecom-state" className="field-label">
            {t('metaTitle')}
          </h2>
          <div className="mt-3">
            <StateSlot
              state={state}
              density="compact"
              labels={{
                loading: common('retry'),
                empty: statusLine('noData'),
                error: statusLine('unavailable'),
                partial: statusLine('realData'),
                offline: statusLine('unavailable'),
              }}
              detail={`${answered}/${READS.length} · ${READS.map((read) => read.path).join(' · ')}`}
            >
              <ul className="grid gap-3">
                {READS.map((read, index) => {
                  const result = reads[index];
                  return (
                    <li
                      key={read.id}
                      className="card flex flex-wrap items-center justify-between gap-3 p-4"
                    >
                      <span className="num font-mono text-xs text-ink">{read.path}</span>
                      <span className="flex items-center gap-3">
                        <span className="num text-xs text-ink-soft">
                          {result.ok ? statusLine('realData') : statusLine('unavailable')}
                        </span>
                        <ProvenanceStamp source={read.path} verified={result.ok} />
                        <StatusDot
                          state={result.ok ? 'ok' : 'down'}
                          label={result.ok ? common('live') : statusLine('unavailable')}
                        />
                      </span>
                    </li>
                  );
                })}
              </ul>
            </StateSlot>
          </div>
        </section>

        <section className="mt-8" aria-labelledby="telecom-editor">
          <h2 id="telecom-editor" className="field-label">
            {t('editorTitle')}
          </h2>
          <div className="card mt-3 p-5">
            <MessageEditor />
          </div>
        </section>

        <section className="mt-8" aria-labelledby="telecom-menu">
          <h2 id="telecom-menu" className="field-label">
            {t('menuTitle')}
          </h2>
          <p className="mt-2 text-sm text-ink-soft">{t('menuBody')}</p>
          <div className="mt-3">
            <StateSlot
              state={menu.ok ? 'ready' : 'empty'}
              density="compact"
              labels={{
                loading: common('retry'),
                empty: t('menuUnavailable'),
                error: statusLine('unavailable'),
                partial: statusLine('realData'),
                offline: statusLine('unavailable'),
              }}
              detail={
                menuLanguage
                  ? `/api/v1/ussd/menu/preview?language=${menuLanguage}`
                  : `/api/v1/ussd/menu/preview?language=${locale} · en, fa, ar`
              }
            >
              <Card density="compact">
                <p className="num text-sm whitespace-pre-wrap text-ink" dir="auto">
                  {menu.ok ? menu.data.menu_text : ''}
                </p>
                <div className="mt-3">
                  <ProvenanceStamp source="/api/v1/ussd/menu/preview" verified={menu.ok} />
                </div>
              </Card>
            </StateSlot>
          </div>
        </section>

        <section className="mt-8" aria-labelledby="telecom-languages">
          <h2 id="telecom-languages" className="field-label">
            {t('languagesTitle')}
          </h2>
          <p className="mt-2 text-sm text-ink-soft">{t('languagesBody')}</p>
          <div className="mt-3">
            <StateSlot
              state={
                !languagesResult?.ok
                  ? languagesResult && languagesResult.status === 0
                    ? 'offline'
                    : 'error'
                  : languages.length === 0
                    ? 'empty'
                    : 'ready'
              }
              density="compact"
              labels={{
                loading: common('retry'),
                empty: statusLine('noData'),
                error: statusLine('unavailable'),
                partial: statusLine('realData'),
                offline: statusLine('unavailable'),
              }}
              detail="/api/v1/voice/languages"
            >
              <ul className="flex flex-wrap gap-2">
                {languages.map((language) => (
                  <li
                    key={language}
                    className="num rounded bg-forest/10 px-2 py-1 text-xs text-forest"
                  >
                    {language}
                  </li>
                ))}
              </ul>
            </StateSlot>
          </div>
        </section>

        <section className="mt-8" aria-labelledby="telecom-sms">
          <h2 id="telecom-sms" className="field-label">
            {t('smsDeliveryTitle')}
          </h2>
          <div className="card mt-3 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="num font-mono text-xs text-ink-soft">{SMS_DELIVERY}</span>
              <StatusDot state="down" label={statusLine('unavailable')} />
            </div>
            <p className="mt-2 text-sm text-ink-soft">{t('smsDeliveryBody')}</p>
            <div className="mt-3">
              <ProvenanceStamp source={SMS_DELIVERY} verified={false} method="POST" />
            </div>
          </div>
        </section>

        <section className="mt-8" aria-labelledby="telecom-channels">
          <h2 id="telecom-channels" className="field-label">
            {channels('channels')}
          </h2>
          <ul className="mt-3 grid gap-2">
            {[
              { id: 'ussd', label: channels('ussd'), path: '/api/v1/ussd/status' },
              { id: 'sms', label: channels('sms'), path: null },
              { id: 'voice', label: channels('voice'), path: '/api/v1/voice/status' },
              { id: 'telegram', label: channels('telegram'), path: null },
            ].map((channel) => (
              <li
                key={channel.id}
                className="card flex flex-wrap items-center justify-between gap-3 p-4"
              >
                <span className="text-sm text-ink">{channel.label}</span>
                <span className="num text-xs text-ink-faint">
                  {channel.path ?? statusLine('unavailable')}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
