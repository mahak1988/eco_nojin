import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { readWorkspaceSession, workspaceToken } from '@/lib/workspaces/guard';
import { workspaceGet } from '@/lib/workspaces/server';

import { ledgerCopy } from '../../../admin/_lib/copy';
import { LedgerSurface, RecordList, resolveLedgerState, scalar } from '../../../admin/_lib/surface';

const SLUG = 'workspace-workspace-disputes-dispute_id';
const ROUTE = '/workspace/disputes/{dispute_id}';
const PATH = '/api/v1/disputes/{dispute_id}';

/**
 * `GET /api/v1/disputes/{dispute_id}` —
 * `services/dispute_resolution/routers/disputes.py:61`.
 *
 * `def get_dispute(dispute_id: str, db: Session = Depends(get_db))` returns
 * `{"dispute": d.to_dict(), "events": [e.id for e in svc.events(dispute_id)]}`
 * (`disputes.py:68`), so the payload is one dispute plus the ids of its events.
 *
 * ## This contract has no authentication at all
 *
 * The two neighbours in the same file both take `user=Depends(require_user)` —
 * `create_dispute` at `disputes.py:40` and `list_disputes` at `disputes.py:55` —
 * and this one does not. There is no `Depends` on the function beyond the database
 * session, so `GET /api/v1/disputes/{id}` answers any unauthenticated caller who
 * knows or guesses an id.
 *
 * That is a gateway defect, not a page decision, and it is not in this workstream
 * to fix. What the page does about it is not pretend: it is a read-only surface, it
 * fetches nothing the reader could not already fetch with `curl`, and the upstream
 * gate it reports is *authentication*, not authorisation — which is stated on the
 * page so that a reader, and whoever audits this route, can see that the record in
 * front of them was never access-controlled at the source.
 *
 * The `dispute` object is rendered field by field from whatever `to_dict()` returns
 * rather than from a declared model, because the router declares no `response_model`
 * and the published schema is an untyped object.
 */
interface Fetched {
  ok: boolean;
  status: number;
  data?: Record<string, unknown>;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/workspace/finance/ledger/entries`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/workspace/finance/ledger/entries'),
      languages: languageAlternates('/workspace/finance/ledger/entries'),
    },
  };
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; dispute_id: string }>;
}) {
  const { dispute_id } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('workspace');
  const endpoint = PATH.replace('{dispute_id}', encodeURIComponent(dispute_id));

  const result: Fetched = await workspaceGet<Record<string, unknown>>(
    workspaceToken(await readWorkspaceSession()),
    endpoint,
  );
  const envelope = result.ok ? (result.data ?? {}) : {};
  const dispute =
    typeof envelope.dispute === 'object' && envelope.dispute !== null
      ? (envelope.dispute as Record<string, unknown>)
      : {};
  const events = Array.isArray(envelope.events) ? envelope.events : [];
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="workspace"
      title={meta('title')}
      description={meta('description')}
      path={endpoint}
      slug={SLUG}
      state={state}
      total={result.ok ? 1 : 0}
      ok={result.ok}
      summary={
        result.ok ? (
          <RecordList
            caption={meta('title')}
            fields={[
              { label: c.identifier, value: scalar(dispute.id) },
              { label: c.status, value: scalar(dispute.status) },
              { label: c.type, value: scalar(dispute.reason) },
              { label: c.amount, value: scalar(dispute.amount) },
              { label: c.created, value: scalar(dispute.created_at) },
              { label: c.count, value: events.length },
            ]}
          />
        ) : null
      }
      data={
        result.ok ? (
          <RecordList
            caption={meta('title')}
            fields={[
              { label: c.detail, value: scalar(dispute.description) },
              { label: c.source, value: scalar(dispute.evidence_url) },
              { label: c.member, value: scalar(dispute.opened_by) },
              { label: c.version, value: scalar(dispute.updated_at) },
              {
                label: c.action,
                value: events.length > 0 ? events.map((event) => scalar(event)).join(' · ') : '—',
              },
            ]}
          />
        ) : null
      }
      detail={
        <p className="text-xs text-ink-soft">
          {copy.upstreamGate} <span className="num">{endpoint}</span>
        </p>
      }
    />
  );
}
