import { getTranslations } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import type { ApiResult } from '@/lib/api/client';

/**
 * Honest data states for the public pages. Every public page reads one or more
 * registered gateway endpoints and renders exactly one of these states; nothing
 * here invents a count, a date, a partner or a verification flag.
 */
export type DataState =
  | { kind: 'ready'; path: string; count: number }
  | { kind: 'empty'; path: string }
  | { kind: 'unavailable'; path: string; error: string; status: number };

/** Maps a gateway result plus the number of usable rows onto a render state. */
export function toDataState<T>(path: string, result: ApiResult<T>, count: number): DataState {
  if (!result.ok) {
    return { kind: 'unavailable', path, error: result.error, status: result.status };
  }
  return count > 0 ? { kind: 'ready', path, count } : { kind: 'empty', path };
}

/** A status of 0 means the request never reached the gateway: the device is offline. */
function isOffline(state: Extract<DataState, { kind: 'unavailable' }>): boolean {
  return state.status === 0;
}

export async function DataStateCard({
  state,
  emptyTitle,
  emptyDescription,
}: {
  state: DataState;
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  if (state.kind === 'ready') return null;

  const status = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const offline = await getTranslations('offline');
  const common = await getTranslations('common');

  const offlineMode = state.kind === 'unavailable' && isOffline(state);
  const heading = offlineMode ? offline('title') : template('status');
  const body =
    state.kind === 'empty'
      ? (emptyDescription ?? template('unavailableDescription'))
      : offlineMode
        ? offline('description')
        : template('unavailableDescription');
  const headline = state.kind === 'empty' ? (emptyTitle ?? template('unavailableTitle')) : null;

  return (
    <Card density="compact">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-medium text-ink">{heading}</h3>
        <StatusDot state={offlineMode ? 'down' : 'warn'} label={status('unavailable')} />
      </div>
      {headline ? <p className="mt-2 text-sm font-medium text-ink">{headline}</p> : null}
      <p className="mt-1 text-sm text-ink-soft">{body}</p>
      <p className="mt-3 text-xs text-ink-soft">
        {offlineMode ? offline('code') : common('error')}
        {state.kind === 'unavailable'
          ? ` · ${state.path} · ${state.status || '—'} · ${state.error}`
          : ` · ${state.path} · ${status('noData')}`}
      </p>
      <div className="mt-3">
        <ProvenanceStamp source={state.path} verified={false} method={state.path} />
      </div>
    </Card>
  );
}

/** Provenance footer. Renders only for a real, successful response. */
export async function SourceFooter({ state }: { state: DataState }) {
  if (state.kind !== 'ready') return null;
  const status = await getTranslations('statusLine');

  return (
    <p className="mt-6 flex flex-wrap items-center gap-2 text-xs text-ink-soft">
      <ProvenanceStamp source={state.path} verified method={state.path} />
      <span>{status('realData')}</span>
      <span className="num">{state.count}</span>
    </p>
  );
}

/**
 * Explicit unavailable state for a capability the gateway does not expose.
 * `path` is the route that is missing, never a substitute data source.
 */
export async function UnavailableCapability({
  path,
  contract = true,
}: {
  path: string;
  contract?: boolean;
}) {
  const status = await getTranslations('statusLine');
  const template = await getTranslations('market.template');

  return (
    <>
      <Card density="cozy">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold text-ink">{template('status')}</h2>
          <StatusDot state="down" label={status('unavailable')} />
        </div>
        <p className="mt-2 text-sm text-ink-soft">{template('unavailableDescription')}</p>
        <p className="mt-3 text-xs text-ink-soft">{path}</p>
        <div className="mt-3">
          <ProvenanceStamp source={path} verified={false} method={path} />
        </div>
      </Card>
      {contract ? (
        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('contractTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('contractDescription')}</p>
          </div>
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{template('nextTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('nextDescription')}</p>
          </div>
        </div>
      ) : null}
    </>
  );
}
