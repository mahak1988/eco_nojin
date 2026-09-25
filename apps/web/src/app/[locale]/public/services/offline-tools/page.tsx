import { getTranslations, setRequestLocale } from 'next-intl/server';
import { OwnerFooter } from '@/components/OwnerFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, toDataState } from '../../data-states';

export const dynamic = 'force-dynamic';

const SYNC_STATUS_PATH = '/api/v1/sync/status';

type SyncStatus = {
  status: string;
  mode?: string;
  cloud?: string;
  local_pending_events?: number;
  supabase_connected?: boolean;
  supabase_error?: string | null;
  note?: string;
};

export default async function OfflineToolsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const services = await getTranslations('services');
  const status = await getTranslations('statusLine');
  const common = await getTranslations('common');
  const offline = await getTranslations('offline');

  // Offline-first is not a claim: the registered sync status route reports the
  // real pending-outbox depth and cloud reachability.
  const sync = await apiGet<SyncStatus>(SYNC_STATUS_PATH);
  const state = toDataState(SYNC_STATUS_PATH, sync, sync.ok ? 1 : 0);
  const connected = sync.ok && sync.data.supabase_connected === true;

  return (
    <main className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={SYNC_STATUS_PATH}
          label={services('title')}
          verified={sync.ok}
          method={SYNC_STATUS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{services('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{services('lead')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('what')}</p>
        <p className="mt-3 max-w-2xl text-sm text-ink-soft">{services('audience')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{SYNC_STATUS_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' && sync.ok ? (
          <>
            <div className="grid gap-4 sm:grid-cols-3">
              <Card density="compact">
                <div className="num text-3xl font-semibold text-ink">
                  {sync.data.local_pending_events ?? 0}
                </div>
                <p className="mt-1 text-sm text-ink-soft">{status('noData')}</p>
                <div className="mt-2">
                  <ProvenanceStamp source={SYNC_STATUS_PATH} verified method={SYNC_STATUS_PATH} />
                </div>
              </Card>
              <Card density="compact">
                <p className="font-mono text-sm text-ink">
                  {sync.data.mode ?? status('unavailable')}
                </p>
                <p className="mt-1 text-sm text-ink-soft">{sync.data.cloud ?? common('error')}</p>
              </Card>
              <Card density="compact">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm text-ink">{sync.data.status}</p>
                  <StatusDot
                    state={connected ? 'ok' : 'warn'}
                    label={connected ? common('live') : status('unavailable')}
                  />
                </div>
                {sync.data.supabase_error ? (
                  <p className="mt-1 text-xs text-ink-soft">{sync.data.supabase_error}</p>
                ) : null}
              </Card>
            </div>
            {sync.data.note ? (
              <p className="mt-4 text-xs text-ink-soft">
                {offline('code')} · {sync.data.note}
              </p>
            ) : null}
          </>
        ) : null}
      </section>

      <OwnerFooter />
    </main>
  );
}
