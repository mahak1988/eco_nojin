import { getTranslations } from 'next-intl/server';

import { SiteNav } from '@/components/SiteNav';
import { InstrumentPage } from '@/components/templates/InstrumentPage';
import { apiGet } from '@/lib/api/client';
import { verificationOf } from '@/lib/api/surfaces';

import {
  hydromaLabels,
  number,
  PREVIEW_LIMIT,
  readRows,
  resolveState,
  type SpecEnvelope,
  type SpecParam,
  scalar,
  stateDetail,
  type ToolSpec,
} from './hydroma';
import { ProvenanceBar } from './ProvenanceBar';
import { InputContract, RecordScene, SpecTable } from './Scenes';

/**
 * The five tool families of آ§5.2 that the catalogue does not reach, on the T07
 * archetype.
 *
 * `hydroma/carbon`, `hydroma/climate` and `hydroma/economics` are generated pages
 * owned by `scripts/generate-resource-pages.mjs`; this file is the other five.
 * They share one contract shape, declared rather than inferred:
 *
 *   hydroma_soil.py:428       `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_water.py:266      `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_indices.py:569    `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_mrv.py:141        `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_simulation.py:86  `return {"count": len(_SPECS), "models": _SPECS}`
 *
 * so the rows key is `models` for all five. It is not pluralised from the route
 * name â€” that rule produced `carbons`, `climates` and `economics` on three sibling
 * pages, each of which rendered its empty state over a 200 that had arrived.
 */
export type FamilyKey = 'soil' | 'water' | 'indices' | 'mrv' | 'simulation';

interface Family {
  id: FamilyKey;
  /** Route segment, which is also the router's own tag. */
  segment: string;
  /** The metadata GET that lists the family. */
  listPath: string;
  /** The metadata GET for one tool. */
  detailPath: (modelId: string) => string;
  /** The POST the input panel names. A mutation never gets a page. */
  runPath: (modelId: string) => string;
}

const family = (id: FamilyKey, segment: string): Family => ({
  id,
  segment,
  listPath: `/api/v1/hydroma/${segment}`,
  detailPath: (modelId) => `/api/v1/hydroma/${segment}/${encodeURIComponent(modelId)}`,
  runPath: (modelId) => `/api/v1/hydroma/${segment}/${encodeURIComponent(modelId)}/run`,
});

export const FAMILIES: Record<FamilyKey, Family> = {
  soil: family('soil', 'soil'),
  water: family('water', 'water'),
  indices: family('indices', 'indices'),
  mrv: family('mrv', 'mrv'),
  simulation: family('simulation', 'simulation'),
};

/* -------------------------------------------------------------------------- */
/* The family list                                                            */
/* -------------------------------------------------------------------------- */

/**
 * A real `<form method="get">` that narrows the rows already published.
 *
 * The family list contract takes no query parameter, so the panel does not
 * pretend to be one: it filters the response the gateway already sent, on the
 * server, and the form works with JavaScript disabled because submitting it
 * re-navigates to the same URL with `?q=â€¦`. A control that cannot change the
 * output would be exactly the decoration آ§6 is written against.
 */
async function FilterPanel({ term, path, count }: { term: string; path: string; count: number }) {
  const t = await getTranslations('hydroma.instrument');
  return (
    <form method="get" action="" className="flex flex-col gap-3">
      <label htmlFor="hydroma-family-q" className="text-xs font-medium text-ink">
        q
      </label>
      <input
        id="hydroma-family-q"
        type="search"
        name="q"
        defaultValue={term}
        className="min-h-11 min-w-0 rounded-[var(--radius-s)] border border-line bg-surface px-3 py-2 text-sm text-ink"
      />
      <button
        type="submit"
        className="min-h-11 rounded-[var(--radius-s)] bg-action px-4 py-2 text-sm text-on-action"
      >
        {t('filter')}
      </button>
      <p className="num break-all text-xs text-ink-faint">{path}</p>
      <p className="num text-xs text-ink-soft">{t('shown', { count })}</p>
    </form>
  );
}

/**
 * `family`, not `key`: React consumes `key` on every element, so a `key` prop
 * would be taken by reconciliation and never arrive here â€” the page would fetch
 * `undefined`'s family and render an empty state over a live contract.
 */
export async function ToolFamilyPage({
  locale,
  family,
  term,
}: {
  locale: string;
  family: FamilyKey;
  term: string;
}) {
  const target = FAMILIES[family];
  const [meta, table, labels] = await Promise.all([
    getTranslations(`hydroma.families.${family}`),
    getTranslations('hydroma.table'),
    hydromaLabels(),
  ]);

  const endpoint = target.listPath;
  const result = await apiGet<SpecEnvelope>(endpoint);
  const published = readRows<ToolSpec>(result.ok ? result.data : undefined, 'models');

  const needle = term.trim().toLowerCase();
  const rows = needle
    ? published.filter((spec) =>
        [spec.id, spec.name_en, spec.description, spec.reference]
          .map((field) => String(field ?? '').toLowerCase())
          .some((field) => field.includes(needle)),
      )
    : published;

  const state = resolveState(result, rows.length);
  const visible = rows.slice(0, PREVIEW_LIMIT);

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={meta('title')}
      description={meta('description')}
      labels={labels}
      path={endpoint}
      state={state}
      total={rows.length}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={stateDetail(endpoint, rows.length)}
      input={<FilterPanel term={term} path={endpoint} count={rows.length} />}
      output={
        <div className="flex flex-col gap-3">
          <SpecTable
            specs={visible}
            detailBase={`/${locale}/hydroma/${target.segment}`}
            caption={meta('title')}
            nameHeader={table('name')}
            descriptionHeader={table('description')}
            referenceHeader={table('reference')}
            paramsHeader={table('params')}
          />
          {rows.length > PREVIEW_LIMIT ? (
            <p className="num text-xs text-copper">{table('truncated', { count: rows.length })}</p>
          ) : null}
        </div>
      }
      summary={
        <ProvenanceBar modelVersion={null} calibration={null} confidence={null} run={null} />
      }
      notes={<FamilyNotes family={family} count={published.length} />}
    />
  );
}

/**
 * The method note: what this contract does and does not publish.
 *
 * The five families declare `{id, name_en, description, reference, params}` and
 * nothing else, so there is no model version, no calibration state, no
 * uncertainty and no run identifier anywhere in the response. The bar above says
 * so in four explicit slots; this note says why, and names the POST that does
 * compute â€” a mutation, so it has no page either.
 */
async function FamilyNotes({ family, count }: { family: FamilyKey; count: number }) {
  const [t, meta] = await Promise.all([
    getTranslations('hydroma.instrument'),
    getTranslations(`hydroma.families.${family}`),
  ]);
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm text-ink-soft">{t('familyNote', { count })}</p>
      <p className="text-sm text-ink-soft">{meta('method')}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* One tool                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * One tool: its parameter contract beside its record, under the transparency bar.
 *
 * The four slots are filled only from what the spec publishes. `reference` is a
 * real, cited method â€” `USDA NRCS Soil Texture Triangle`, `Allen et al. 1998
 * (FAO-56)`, `van Genuchten 1980` â€” and it is the calibration lineage, so it
 * goes in the calibration slot. The other three stay empty and say so, because
 * `_SPECS` has no field for any of them.
 */
export async function ToolSpecPage({
  locale,
  family,
  modelId,
}: {
  locale: string;
  family: FamilyKey;
  modelId: string;
}) {
  const target = FAMILIES[family];
  const [meta, table, labels] = await Promise.all([
    getTranslations(`hydroma.families.${family}`),
    getTranslations('hydroma.table'),
    hydromaLabels(),
  ]);

  const endpoint = target.detailPath(modelId);
  const result = await apiGet<ToolSpec>(endpoint);
  const spec = result.ok ? result.data : null;
  const params: SpecParam[] = Array.isArray(spec?.params) ? (spec?.params ?? []) : [];
  const state = resolveState(result, spec ? 1 : 0);

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={scalar(spec?.name_en) || scalar(spec?.id) || modelId}
      description={scalar(spec?.description)}
      labels={labels}
      path={endpoint}
      state={state}
      total={spec ? 1 : 0}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={stateDetail(endpoint, spec ? 1 : 0)}
      input={<InputContract params={params} runPath={target.runPath(modelId)} />}
      output={
        <div className="flex flex-col gap-3">
          <RecordScene
            caption={meta('title')}
            entries={[
              { label: 'id', value: scalar(spec?.id) },
              { label: 'name_en', value: scalar(spec?.name_en) },
              { label: 'description', value: scalar(spec?.description) },
              { label: 'reference', value: scalar(spec?.reference) },
              { label: table('params'), value: number(params.length) },
            ]}
          />
          <p className="text-xs text-ink-soft">{meta('method')}</p>
        </div>
      }
      summary={
        <ProvenanceBar
          modelVersion={null}
          calibration={scalar(spec?.reference) || null}
          confidence={null}
          run={null}
        />
      }
      notes={<SpecNote count={params.length} path={target.runPath(modelId)} />}
    />
  );
}

async function SpecNote({ count, path }: { count: number; path: string }) {
  const t = await getTranslations('hydroma.instrument');
  return <p className="text-sm text-ink-soft">{t('specNote', { count, path })}</p>;
}
