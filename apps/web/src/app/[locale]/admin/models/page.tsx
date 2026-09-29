import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

import { ledgerCopy } from '../_lib/copy';
import {
  LedgerSurface,
  LedgerTable,
  PlaceholderNotice,
  PREVIEW_LIMIT,
  readRows,
  resolveLedgerState,
  scalar,
  UnmeasuredCell,
} from '../_lib/surface';

const SLUG = 'admin-admin-models';
const ROUTE = '/admin/models';
const PATH = '/api/v1/admin/models';

/**
 * `GET /api/v1/admin/models` — `services/api_gateway/routers/admin_models.py:68`.
 *
 * `response_model=List[ModelResponse]`, so the payload is a bare array.
 * `ModelResponse` is declared at `admin_models.py:18` with `name`, `size`,
 * `modified_at`, `digest`, `family`, `parameter_size`, `quantization_level` and
 * `running`.
 *
 * ## No field in this payload is a measurement
 *
 * The handler is `return list(MODEL_STORE.values())` (`admin_models.py:71`), and
 * `MODEL_STORE` is a three-entry dict literal declared at `admin_models.py:33-65`
 * under the comment "Mock model store (replace with actual Ollama client)". Nothing
 * queries Ollama. The values are invented: the `size` and `modified_at` fields are
 * constants chosen by the author, and the `digest` fields are truncated to
 * `sha256:abc123...`, `sha256:def456...` and `sha256:ghi789...`, which are not
 * digests of anything.
 *
 * The names are the one field that is not fabricated, because they are also the
 * dict keys and are what a request for a record would be keyed on — but they still
 * describe the mock, not an installed model. So the page lists the names, labels
 * every other column as not measured, and states the reason above the table rather
 * than presenting six invented constants in a table that looks like an inventory.
 *
 * `components/admin/admin-sections.ts` already records the same conclusion for a
 * neighbouring capability: "services/api_gateway/routers/admin_models.py …" is not
 * in its list, but `admin-overview` and `admin-channel-health` are set to
 * `endpoint: null` for exactly this reason.
 */
interface ModelRow {
  name?: string;
  size?: string;
  modified_at?: string;
  digest?: string;
  family?: string | null;
  parameter_size?: string | null;
  quantization_level?: string | null;
  running?: boolean;
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
      url: `${BASE_URL}/${locale}${ROUTE}`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('admin');

  const result = await adminGet<ModelRow[]>(adminToken(await readAdminSession()), PATH);
  const rows = readRows<ModelRow>(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, rows.length);
  const visible = rows.slice(0, PREVIEW_LIMIT);
  const c = copy.columns;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="admin"
      title={meta('title')}
      description={meta('description')}
      path={PATH}
      slug={SLUG}
      state={state}
      total={rows.length}
      ok={result.ok}
      stateDetail={`${PATH} · ${rows.length}`}
      data={
        <div className="flex flex-col gap-3">
          <PlaceholderNotice heading={copy.placeholderHeading} body={copy.placeholderBody} />
          <LedgerTable<ModelRow>
            columns={[
              { key: 'name', header: c.name, render: (row) => scalar(row.name) },
              {
                key: 'family',
                header: c.group,
                render: () => <UnmeasuredCell label={copy.notMeasured} />,
              },
              {
                key: 'size',
                header: c.value,
                render: () => <UnmeasuredCell label={copy.notMeasured} />,
              },
              {
                key: 'digest',
                header: c.key,
                render: () => <UnmeasuredCell label={copy.notMeasured} />,
              },
              {
                key: 'running',
                header: c.status,
                render: () => <UnmeasuredCell label={copy.notMeasured} />,
              },
            ]}
            rows={visible}
            rowKey={(row) => String(row.name ?? '')}
            caption={meta('title')}
            emptyLabel={copy.emptyLabel}
          />
        </div>
      }
      detail={
        <p className="num text-xs text-ink-faint">
          {PATH} — services/api_gateway/routers/admin_models.py:33
        </p>
      }
    />
  );
}
