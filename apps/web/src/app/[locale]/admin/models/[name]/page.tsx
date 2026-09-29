import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

import { ledgerCopy } from '../../_lib/copy';
import {
  LedgerSurface,
  PlaceholderNotice,
  record,
  resolveLedgerState,
  scalar,
  segment,
  UnmeasuredCell,
} from '../../_lib/surface';

const SLUG = 'admin-admin-models-name';
const ROUTE = '/admin/models/{name}';
const PATH = '/api/v1/admin/models/{name}';

/**
 * `GET /api/v1/admin/models/{name}` — `services/api_gateway/routers/admin_models.py:76`.
 *
 * `response_model=ModelResponse`, so the payload is one record. The handler looks
 * the name up in `MODEL_STORE` and raises `404` when it is absent
 * (`admin_models.py:81-82`).
 *
 * The store is the same three-entry mock literal as the index, declared at
 * `admin_models.py:33-65`. Only `name` is not an invented constant, so the page
 * renders the name and labels `size`, `modified_at`, `digest`, `family`,
 * `parameter_size`, `quantization_level` and `running` as not measured. The
 * segment is resolved from the route parameter rather than the literal `{name}`.
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
      url: `${BASE_URL}/${locale}/admin/models`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/admin/models'),
      languages: languageAlternates('/admin/models'),
    },
  };
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; name: string }>;
}) {
  const { name } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('admin');
  const endpoint = PATH.replace('{name}', segment(name));

  const result: Fetched = await adminGet<Record<string, unknown>>(
    adminToken(await readAdminSession()),
    endpoint,
  );
  const payload = record(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
  const c = copy.columns;
  const notMeasured = <UnmeasuredCell label={copy.notMeasured} />;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="admin"
      title={meta('title')}
      description={meta('description')}
      path={endpoint}
      slug={SLUG}
      state={state}
      total={result.ok ? 1 : 0}
      ok={result.ok}
      stateDetail={result.ok ? undefined : `${endpoint} · ${result.status}`}
      data={
        result.ok ? (
          <div className="flex flex-col gap-3">
            <PlaceholderNotice heading={copy.placeholderHeading} body={copy.placeholderBody} />
            <dl className="grid gap-2 sm:grid-cols-[minmax(0,14rem)_minmax(0,1fr)]">
              <dt className="text-xs text-ink-soft">{c.name}</dt>
              <dd className="num text-sm text-ink">{scalar(payload.name)}</dd>
              {(
                [
                  { field: 'size', label: c.value },
                  { field: 'modified_at', label: c.updated },
                  { field: 'digest', label: c.key },
                  { field: 'family', label: c.group },
                  { field: 'parameter_size', label: c.count },
                  { field: 'quantization_level', label: c.type },
                  { field: 'running', label: c.status },
                ] as const
              ).map((entry) => (
                <div key={entry.field} className="contents">
                  <dt className="text-xs text-ink-soft">{entry.label}</dt>
                  <dd className="text-sm">{notMeasured}</dd>
                </div>
              ))}
            </dl>
          </div>
        ) : null
      }
      detail={
        <p className="num text-xs text-ink-faint">
          {endpoint} — services/api_gateway/routers/admin_models.py:33
        </p>
      }
    />
  );
}
