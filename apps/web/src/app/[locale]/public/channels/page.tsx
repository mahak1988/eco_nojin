import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const USSD_STATUS_PATH = '/api/v1/ussd/status';
const USSD_MENU_PATH = '/api/v1/ussd/menu/preview';
const VOICE_STATUS_PATH = '/api/v1/voice/status';
const VOICE_LANGUAGES_PATH = '/api/v1/voice/languages';
const SYNC_PATH = '/api/v1/sync/status';

type UssdStatus = {
  status: string;
  ussd_code: string;
  requires_gateway: boolean;
  blocked_by_upstream: boolean;
  notes: string;
};

type UssdMenu = {
  ussd_code: string;
  menu_text: string;
  session_state: string;
  greeting: string;
  requires_gateway: boolean;
  registered: boolean;
  error?: string;
  note?: string;
};

type VoiceStatus = {
  status: string;
  requires_gateway: boolean;
  available_languages: number;
  supported_languages?: string[];
  notes?: string;
};

type VoiceLanguages = { count: number; languages: { code: string; name: string }[] };

type SyncStatus = {
  status: string;
  supabase_connected?: boolean;
  supabase_error?: string | null;
  local_pending_events?: number;
};

const TITLES: Record<string, string> = { fa: 'کانال‌های دسترسی', en: 'Access Channels' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'وضعیت واقعی کانال‌های USSD، صوت و همگام‌سازی',
  en: 'The real USSD, voice, and sync channel status',
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
      url: `${BASE_URL}/${locale}/public/channels`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/channels`,
      languages: {
        fa: `${BASE_URL}/fa/public/channels`,
        en: `${BASE_URL}/en/public/channels`,
      },
    },
  };
}

export default async function ChannelsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.channels');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const [ussd, menu, voice, languages, sync] = await Promise.all([
    apiGet<UssdStatus>(USSD_STATUS_PATH),
    apiGet<UssdMenu>(USSD_MENU_PATH),
    apiGet<VoiceStatus>(VOICE_STATUS_PATH),
    apiGet<VoiceLanguages>(VOICE_LANGUAGES_PATH),
    apiGet<SyncStatus>(SYNC_PATH),
  ]);
  const ussdState = toDataState(USSD_STATUS_PATH, ussd, ussd.ok ? 1 : 0);
  const menuState = toDataState(USSD_MENU_PATH, menu, menu.ok ? 1 : 0);
  const voiceState = toDataState(VOICE_STATUS_PATH, voice, voice.ok ? 1 : 0);
  const languagesState = toDataState(
    VOICE_LANGUAGES_PATH,
    languages,
    languages.ok ? languages.data.languages.length : 0,
  );
  const syncState = toDataState(SYNC_PATH, sync, sync.ok ? 1 : 0);

  const cards = [
    { id: 'ussd', label: t('ussdLabel'), body: t('ussdBody'), state: ussdState },
    { id: 'voice', label: t('voiceLabel'), body: t('voiceBody'), state: voiceState },
    { id: 'sms', label: t('smsLabel'), body: t('smsBody'), state: null },
    { id: 'web', label: t('webLabel'), body: t('webBody'), state: null },
    { id: 'whatsapp', label: t('whatsappLabel'), body: t('whatsappBody'), state: null },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={USSD_STATUS_PATH}
          label={title}
          verified={ussd.ok}
          method={USSD_STATUS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <div className="grid gap-4 sm:grid-cols-2">
          {cards.map((card) => (
            <Card key={card.id} density="cozy">
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-semibold text-ink">{card.label}</h2>
                {card.state ? null : <StatusDot state="down" label={status('unavailable')} />}
              </div>
              <p className="mt-2 text-sm text-ink-soft">{card.body}</p>
              {card.state ? (
                <div className="mt-3">
                  <DataStateCard state={card.state} />
                  <SourceFooter state={card.state} />
                </div>
              ) : (
                <p className="mt-3 text-xs text-ink-soft">
                  {template('status')} · {status('unavailable')}
                </p>
              )}
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{USSD_STATUS_PATH}</h2>
        <DataStateCard state={ussdState} />
        {ussdState.kind === 'ready' && ussd.ok ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card density="compact">
              <div className="num font-mono text-2xl text-ink">{ussd.data.ussd_code}</div>
              <p className="mt-1 text-sm text-ink-soft">{ussd.data.status}</p>
            </Card>
            <Card density="compact">
              <p className="text-sm text-ink">
                {ussd.data.requires_gateway ? status('unavailable') : common('live')}
              </p>
              <p className="mt-1 text-xs text-ink-soft">{ussd.data.notes}</p>
            </Card>
            <Card density="compact">
              <StatusDot
                state={ussd.data.blocked_by_upstream ? 'down' : 'ok'}
                label={String(ussd.data.blocked_by_upstream)}
              />
            </Card>
          </div>
        ) : null}
        <SourceFooter state={ussdState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{USSD_MENU_PATH}</h2>
        <DataStateCard state={menuState} />
        {menuState.kind === 'ready' && menu.ok ? (
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="num font-mono text-sm text-ink">{menu.data.ussd_code}</p>
              <StatusDot
                state={menu.data.registered ? 'ok' : 'warn'}
                label={menu.data.session_state}
              />
            </div>
            <div className="prose mt-3 max-w-none whitespace-pre-wrap text-sm text-ink-soft">
              {menu.data.menu_text}
            </div>
            {menu.data.note ? <p className="mt-3 text-xs text-ink-soft">{menu.data.note}</p> : null}
            <div className="mt-3">
              <ProvenanceStamp source={USSD_MENU_PATH} verified method={USSD_MENU_PATH} />
            </div>
          </Card>
        ) : null}
        <SourceFooter state={menuState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{VOICE_STATUS_PATH}</h2>
        <DataStateCard state={voiceState} />
        {voiceState.kind === 'ready' && voice.ok ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card density="compact">
              <p className="text-sm text-ink">{voice.data.status}</p>
              <p className="mt-1 text-xs text-ink-soft">
                {voice.data.requires_gateway ? status('unavailable') : common('live')}
              </p>
            </Card>
            <Card density="compact">
              <div className="num text-3xl font-semibold text-ink">
                {voice.data.available_languages}
              </div>
              <p className="mt-1 text-sm text-ink-soft">{VOICE_LANGUAGES_PATH}</p>
            </Card>
            <Card density="compact">
              {voice.data.notes ? (
                <p className="text-sm text-ink-soft">{voice.data.notes}</p>
              ) : null}
            </Card>
          </div>
        ) : null}
        <SourceFooter state={voiceState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{VOICE_LANGUAGES_PATH}</h2>
        <DataStateCard state={languagesState} />
        {languagesState.kind === 'ready' && languages.ok ? (
          <div className="flex flex-wrap gap-2">
            {languages.data.languages.map((entry) => (
              <span key={entry.code} className="rounded bg-forest/10 px-2 py-1 text-xs text-forest">
                {entry.code} · {entry.name}
              </span>
            ))}
          </div>
        ) : null}
        <SourceFooter state={languagesState} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{SYNC_PATH}</h2>
        <DataStateCard state={syncState} />
        {syncState.kind === 'ready' && sync.ok ? (
          <Card density="compact">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-ink">{sync.data.status}</p>
              <StatusDot
                state={sync.data.supabase_connected ? 'ok' : 'warn'}
                label={sync.data.supabase_connected ? common('live') : status('unavailable')}
              />
            </div>
            {sync.data.supabase_error ? (
              <p className="mt-2 text-xs text-ink-soft">{sync.data.supabase_error}</p>
            ) : null}
            <div className="mt-3">
              <ProvenanceStamp source={SYNC_PATH} verified method={SYNC_PATH} />
            </div>
          </Card>
        ) : null}
        <SourceFooter state={syncState} />
      </section>
    </main>
  );
}
