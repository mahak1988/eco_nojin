import Link from 'next/link';
import { getTranslations } from 'next-intl/server';

import { SiteNav } from '@/components/SiteNav';
import { InstrumentPage } from '@/components/templates/InstrumentPage';
import { Badge } from '@/components/ui/Badge';
import { type ApiResult, apiGet } from '@/lib/api/client';
import { verificationOf } from '@/lib/api/surfaces';

import {
  hydromaLabels,
  type ModelMeta,
  number,
  PREVIEW_LIMIT,
  readRows,
  resolveState,
  type SlaughterhouseStatus,
  scalar,
  stateDetail,
  type ValidationReport,
  type ValidationStatus,
} from './hydroma';
import { ProvenanceBar } from './ProvenanceBar';
import { RecordScene } from './Scenes';

/**
 * The model registry of `hydroma_dashboard.py` â€” the one surface in this subtree
 * whose response publishes a model version.
 *
 * Measured against the live registry rather than the Pydantic model, because the
 * difference is the whole page:
 *
 *   - `ModelMeta` declares `inputs`, `outputs` and `performance`
 *     (`hydroma_dashboard.py:73-76`), but `_discover_models` never sets them, so
 *     all three arrive as the empty list for every one of the 39 models. The input
 *     contract of a model is therefore **not published** anywhere in this
 *     response, and neither is `BenchmarkData.accuracy_score` â€” the only field in
 *     the whole gateway that would have been a confidence figure.
 *   - `validation.status` is not a test result. `_determine_validation_status`
 *     (`:685-706`) returns the model's own declared `status` field whenever a test
 *     fixture file exists, and `unvalidated` otherwise. It is a declaration, and
 *     the page labels it as one.
 *   - `validation.last_validated` is `ValidationStatus(status=â€¦)` with no second
 *     argument (`:704`), so `last_validated` is `None` for every model. There is
 *     no run date.
 *
 * The transparency bar reflects that: version and calibration are real, the
 * confidence interval and the run identifier say that the contract does not
 * publish them.
 */
const LIST_PATH = '/api/v1/hydroma/models';

/** A frequency table over a field the response publishes on every row. */
function tally(values: readonly (string | null | undefined)[]): string {
  const counts = new Map<string, number>();
  for (const value of values) {
    if (value === null || value === undefined || value === '') continue;
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  const entries = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return '';
  return entries.map(([value, count]) => `${value} (${count})`).join(' آ· ');
}

/* -------------------------------------------------------------------------- */
/* The registry table                                                         */
/* -------------------------------------------------------------------------- */

function ModelTable({
  rows,
  base,
  caption,
  headers,
}: {
  rows: readonly ModelMeta[];
  base: string;
  caption: string;
  headers: {
    name: string;
    category: string;
    version: string;
    language: string;
    status: string;
    reference: string;
  };
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="text-start text-xs text-ink-faint">{caption}</caption>
        <thead>
          <tr className="border-b border-line-strong">
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              id
            </th>
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              {headers.name}
            </th>
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              {headers.category}
            </th>
            <th scope="col" className="py-2 pe-3 text-end text-xs font-semibold text-ink-soft">
              {headers.version}
            </th>
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              {headers.language}
            </th>
            <th scope="col" className="py-2 pe-3 text-start text-xs font-semibold text-ink-soft">
              {headers.status}
            </th>
            <th scope="col" className="py-2 text-start text-xs font-semibold text-ink-soft">
              {headers.reference}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-line align-top">
              <th scope="row" className="num py-2 pe-3 text-start font-normal">
                <Link
                  href={`${base}/${encodeURIComponent(row.id)}`}
                  className="text-action underline decoration-line-strong underline-offset-2"
                >
                  {row.id}
                </Link>
              </th>
              <td className="py-2 pe-3 text-ink">{scalar(row.name)}</td>
              <td className="py-2 pe-3 text-ink-soft">{scalar(row.category)}</td>
              <td className="num py-2 pe-3 text-end text-ink">{scalar(row.version)}</td>
              <td className="py-2 pe-3 text-ink-soft">{scalar(row.language)}</td>
              <td className="py-2 pe-3">
                <Badge tone={row.status === 'stable' ? 'success' : 'neutral'} density="dense">
                  {scalar(row.status)}
                </Badge>
              </td>
              <td className="py-2 text-ink-soft">{scalar(row.reference)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* The three filters the contract itself declares                               */
/* -------------------------------------------------------------------------- */

/**
 * The gateway's own query parameters, as a no-JS form.
 *
 * `hydroma_dashboard.py:716-718` declares `category`, `status` and `language`, and
 * `:723-728` filters on them server-side. The option lists are read off the
 * unfiltered response rather than invented, so a value the registry never declares
 * cannot appear in the picker. This is the T07 input panel doing exactly what آ§6
 * says it is for: a control that changes the output scene.
 */
async function RegistryFilters({
  base,
  path,
  category,
  status,
  language,
  options,
}: {
  base: string;
  path: string;
  category: string;
  status: string;
  language: string;
  options: { category: string[]; status: string[]; language: string[] };
}) {
  const t = await getTranslations('hydroma.registry');
  const select = (name: string, label: string, current: string, values: readonly string[]) => (
    <div className="flex flex-col gap-1">
      <label htmlFor={`hydroma-filter-${name}`} className="text-xs font-medium text-ink">
        {label}
      </label>
      <select
        id={`hydroma-filter-${name}`}
        name={name}
        defaultValue={current}
        className="min-h-11 rounded-[var(--radius-s)] border border-line bg-surface px-2 py-2 text-sm text-ink"
      >
        <option value="">{t('all')}</option>
        {values.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <form method="get" action={base} className="flex flex-col gap-3">
      {select('category', t('category'), category, options.category)}
      {select('status', t('status'), status, options.status)}
      {select('language', t('language'), language, options.language)}
      <button
        type="submit"
        className="min-h-11 rounded-[var(--radius-s)] bg-action px-4 py-2 text-sm text-on-action"
      >
        {t('apply')}
      </button>
      <p className="num break-all text-xs text-ink-faint">{path}</p>
    </form>
  );
}

/* -------------------------------------------------------------------------- */
/* The registry page                                                          */
/* -------------------------------------------------------------------------- */

export async function ModelListPage({
  locale,
  category,
  status,
  language,
}: {
  locale: string;
  category: string;
  status: string;
  language: string;
}) {
  const [meta, table, labels, filters] = await Promise.all([
    getTranslations('hydroma.pages.models'),
    getTranslations('hydroma.table'),
    hydromaLabels(),
    getTranslations('hydroma.registry'),
  ]);

  // The unfiltered list is always fetched: it is the option list for the panel,
  // and on an unfiltered visit it is also the data.
  const unfiltered = await apiGet<ModelMeta[]>(LIST_PATH);
  const all = readRows<ModelMeta>(unfiltered.ok ? unfiltered.data : undefined);

  const active = [category, status, language].filter((value) => value.length > 0);
  const query = new URLSearchParams();
  if (category) query.set('category', category);
  if (status) query.set('status', status);
  if (language) query.set('language', language);
  const endpoint = active.length > 0 ? `${LIST_PATH}?${query.toString()}` : LIST_PATH;

  // A filtered visit asks the gateway, not the page: the URL on the provenance
  // stamp has to be the one that produced the rows, or the stamp names a contract
  // the reader did not call.
  let filtered: ApiResult<ModelMeta[]>;
  if (active.length > 0) {
    filtered = await apiGet<ModelMeta[]>(endpoint);
  } else if (unfiltered.ok) {
    filtered = { ok: true, data: all, status: unfiltered.status };
  } else {
    filtered = { ok: false, error: unfiltered.error, status: unfiltered.status };
  }
  const rows = readRows<ModelMeta>(filtered.ok ? filtered.data : undefined);
  const state = resolveState(filtered, rows.length);
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
      ok={filtered.ok}
      verified={filtered.ok && verificationOf(filtered.data)}
      stateDetail={stateDetail(endpoint, rows.length)}
      input={
        <RegistryFilters
          base={`/${locale}/hydroma/models`}
          path={endpoint}
          category={category}
          status={status}
          language={language}
          options={{
            category: [...new Set(all.map((model) => scalar(model.category)))].sort(),
            status: [...new Set(all.map((model) => scalar(model.status)))].sort(),
            language: [...new Set(all.map((model) => scalar(model.language)))].sort(),
          }}
        />
      }
      output={
        <div className="flex flex-col gap-3">
          <ModelTable
            rows={visible}
            base={`/${locale}/hydroma/models`}
            caption={meta('title')}
            headers={{
              name: table('name'),
              category: table('category'),
              version: table('version'),
              language: table('language'),
              status: table('status'),
              reference: table('reference'),
            }}
          />
          {rows.length > PREVIEW_LIMIT ? (
            <p className="num text-xs text-copper">{table('truncated', { count: rows.length })}</p>
          ) : null}
        </div>
      }
      summary={
        <ProvenanceBar
          modelVersion={tally(rows.map((model) => model.version)) || null}
          calibration={tally(rows.map((model) => model.validation?.status)) || null}
          confidence={null}
          run={
            tally(
              rows.flatMap((model) => [
                model.validation?.last_validated ?? null,
                ...(model.performance ?? []).map((entry) => entry.last_run ?? null),
              ]),
            ) || null
          }
        />
      }
      notes={<RegistryNote count={all.length} />}
      detail={
        active.length === 0 ? (
          <p className="text-xs text-ink-soft">{filters('noFilter')}</p>
        ) : (
          <p className="text-xs text-ink-soft">
            {filters('filtered')} <span className="num">{active.join(' آ· ')}</span>
          </p>
        )
      }
    />
  );
}

async function RegistryNote({ count }: { count: number }) {
  const t = await getTranslations('hydroma.registry');
  return <p className="text-sm text-ink-soft">{t('note', { count })}</p>;
}

/* -------------------------------------------------------------------------- */
/* One model                                                                  */
/* -------------------------------------------------------------------------- */

export async function ModelDetailPage({ locale, modelId }: { locale: string; modelId: string }) {
  const [meta, table, labels] = await Promise.all([
    getTranslations('hydroma.pages.model'),
    getTranslations('hydroma.table'),
    hydromaLabels(),
  ]);

  const endpoint = `/api/v1/hydroma/models/${encodeURIComponent(modelId)}`;
  const result = await apiGet<ModelMeta>(endpoint);
  const model = result.ok ? result.data : null;
  const state = resolveState(result, model ? 1 : 0);
  const accuracy = (model?.performance ?? [])
    .map((entry) => entry.accuracy_score)
    .filter((value): value is number => typeof value === 'number');
  const runs = (model?.performance ?? [])
    .map((entry) => entry.last_run)
    .filter((value): value is string => typeof value === 'string' && value.length > 0);

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={scalar(model?.name) || modelId}
      description={scalar(model?.description)}
      labels={labels}
      path={endpoint}
      state={state}
      total={model ? 1 : 0}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={stateDetail(endpoint, model ? 1 : 0)}
      input={<ModelInputPanel inputs={model?.inputs ?? []} runPath={`${endpoint}/run`} />}
      output={
        <div className="flex flex-col gap-3">
          <RecordScene
            caption={meta('title')}
            entries={[
              { label: 'id', value: scalar(model?.id) },
              { label: table('category'), value: scalar(model?.category) },
              { label: table('version'), value: scalar(model?.version) },
              { label: table('language'), value: scalar(model?.language) },
              { label: table('status'), value: scalar(model?.status) },
              { label: table('reference'), value: scalar(model?.reference) },
              { label: 'repo_path', value: scalar(model?.repo_path) },
              { label: 'test_file', value: scalar(model?.test_file) },
              {
                label: 'validation',
                value: validationText(model?.validation),
              },
              { label: table('testCases'), value: number(model?.test_cases?.length ?? 0) },
              { label: 'outputs', value: number(model?.outputs?.length ?? 0) },
            ]}
          />
          <OutputList outputs={model?.outputs ?? []} />
        </div>
      }
      summary={
        <ProvenanceBar
          modelVersion={scalar(model?.version) || null}
          calibration={calibrationText(model)}
          confidence={
            accuracy.length > 0
              ? `${number(Math.min(...accuracy))} â€“ ${number(Math.max(...accuracy))}`
              : null
          }
          run={runs.length > 0 ? runs.join(' آ· ') : null}
        />
      }
      notes={<ModelNote model={model} />}
    />
  );
}

/** `validated` is a declared field, not a test outcome, and is labelled so. */
function validationText(status: ValidationStatus | undefined): string {
  if (!status?.status) return '';
  return status.last_validated ? `${status.status} آ· ${status.last_validated}` : status.status;
}

function calibrationText(model: ModelMeta | null): string | null {
  if (!model) return null;
  const parts = [scalar(model.reference), model.validation?.status].filter(Boolean);
  return parts.length > 0 ? parts.join(' آ· ') : null;
}

async function ModelInputPanel({
  inputs,
  runPath,
}: {
  inputs: NonNullable<ModelMeta['inputs']>;
  runPath: string;
}) {
  const t = await getTranslations('hydroma.registry');
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-ink-soft">
        {inputs.length === 0 ? t('noInputs') : t('inputCount', { count: inputs.length })}
      </p>
      {inputs.map((input) => (
        <div
          key={input.name}
          className="rounded-[var(--radius-s)] border border-line bg-surface px-3 py-2"
        >
          <span className="num text-sm text-ink">{input.name}</span>
          <p className="mt-1 text-xs text-ink-soft">{input.description}</p>
          <p className="num mt-1 text-xs text-ink-faint">
            {input.type}
            {input.unit ? ` آ· ${input.unit}` : ''}
          </p>
        </div>
      ))}
      <p className="num break-all text-xs text-ink-soft">{t('runIsPost', { path: runPath })}</p>
    </div>
  );
}

async function OutputList({ outputs }: { outputs: NonNullable<ModelMeta['outputs']> }) {
  if (outputs.length === 0) return null;
  return (
    <ul className="flex flex-col gap-1">
      {outputs.map((output) => (
        <li key={output.name} className="text-xs text-ink-soft">
          <span className="num text-ink">{output.name}</span> آ· {output.type}
          {output.unit ? ` آ· ${output.unit}` : ''} آ· {output.description}
        </li>
      ))}
    </ul>
  );
}

async function ModelNote({ model }: { model: ModelMeta | null }) {
  const t = await getTranslations('hydroma.registry');
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm text-ink-soft">{t('declaredNotExecuted')}</p>
      {model?.validation?.message ? (
        <p className="text-sm text-ink-soft">{scalar(model.validation.message)}</p>
      ) : null}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* One model's validation report                                               */
/* -------------------------------------------------------------------------- */

/**
 * The report is **declared, not executed** â€” and the page says so in a badge.
 *
 * `hydroma_dashboard.py:763-789` is explicit in its own comments: *"In a real
 * implementation, this would run the actual tests / For now, return mock report
 * based on test case definitions."* Every fixture that has an `expected` key is
 * marked `passed` without anything running, `failed` is therefore always `0`, and
 * `overall_status` is `"passed"` whenever `failed == 0`. Rendering that as a
 * validation result would be the plan's forbidden move: presenting a simulated
 * value as a real one. The badge says `declared`; the numbers are the contract's.
 */
export async function ModelValidationPage({
  locale,
  modelId,
}: {
  locale: string;
  modelId: string;
}) {
  const [meta, labels, registry] = await Promise.all([
    getTranslations('hydroma.pages.modelValidation'),
    hydromaLabels(),
    getTranslations('hydroma.registry'),
  ]);

  const endpoint = `/api/v1/hydroma/models/${encodeURIComponent(modelId)}/validation`;
  const result = await apiGet<ValidationReport>(endpoint);
  const report = result.ok ? result.data : null;
  const state = resolveState(result, report ? 1 : 0);
  const declared = report?.details ?? [];

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={meta('title')}
      description={meta('description')}
      labels={labels}
      path={endpoint}
      state={state}
      total={report ? 1 : 0}
      ok={result.ok}
      verified={false}
      stateDetail={stateDetail(endpoint, report ? 1 : 0)}
      input={<DeclaredCases cases={declared} runPath={endpoint} />}
      output={
        <div className="flex flex-col gap-3">
          <p>
            <Badge tone="warn" density="cozy" dot>
              {registry('declaredBadge')}
            </Badge>
          </p>
          <RecordScene
            caption={meta('title')}
            entries={[
              { label: 'model_id', value: scalar(report?.model_id) },
              { label: 'overall_status', value: scalar(report?.overall_status) },
              { label: 'test_cases_total', value: number(report?.test_cases_total ?? 0) },
              { label: 'test_cases_passed', value: number(report?.test_cases_passed ?? 0) },
              { label: 'test_cases_failed', value: number(report?.test_cases_failed ?? 0) },
              { label: 'test_cases_skipped', value: number(report?.test_cases_skipped ?? 0) },
              { label: 'generated_at', value: scalar(report?.generated_at) },
            ]}
          />
        </div>
      }
      summary={
        <ProvenanceBar
          modelVersion={null}
          calibration={report ? `${report.overall_status}` : null}
          confidence={null}
          run={scalar(report?.generated_at) || null}
        />
      }
      notes={<p className="text-sm text-ink-soft">{registry('mockNote')}</p>}
    />
  );
}

async function DeclaredCases({
  cases,
  runPath,
}: {
  cases: readonly Record<string, unknown>[];
  runPath: string;
}) {
  const t = await getTranslations('hydroma.registry');
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-ink-soft">{t('declaredInput', { count: cases.length })}</p>
      <ul className="flex flex-col gap-2">
        {cases.map((entry, index) => (
          <li
            key={String(entry.test_case ?? index)}
            className="rounded-[var(--radius-s)] border border-line bg-surface px-3 py-2"
          >
            <span className="num text-sm text-ink">{String(entry.test_case ?? index)}</span>
            <p className="mt-1 text-xs text-ink-soft">{scalar(entry.message)}</p>
          </li>
        ))}
      </ul>
      <p className="num break-all text-xs text-ink-faint">{runPath}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* The slaughterhouse roll-up                                                 */
/* -------------------------------------------------------------------------- */

/**
 * `hydroma_dashboard.py:832-861` counts the registry's own declared `status` field
 * into five buckets and stamps `last_run` with `datetime.now(UTC)`.
 *
 * Two honest readings, both stated on the page:
 *
 *   - the buckets are a tally of *declared* metadata, not of executed validation.
 *     `_discover_models` uses `validated` for two models, `stable` for five and
 *     `unvalidated` for the 29 with no test fixture, and the endpoint buckets on
 *     that field verbatim;
 *   - `last_run` is the moment this GET was served, not the moment a model was last
 *     executed. It is still the only timestamp the contract publishes, so it goes
 *     in the run slot â€” labelled as the read, which is what it is.
 *
 * The endpoint takes no parameters, so the input panel states the contract and how
 * the buckets are derived rather than carrying a control that cannot change the
 * output.
 */
export async function SlaughterhousePage({ locale }: { locale: string }) {
  const [meta, labels, registry] = await Promise.all([
    getTranslations('hydroma.pages.slaughterhouse'),
    hydromaLabels(),
    getTranslations('hydroma.registry'),
  ]);

  const endpoint = '/api/v1/hydroma/slaughterhouse/status';
  const result = await apiGet<SlaughterhouseStatus>(endpoint);
  const status = result.ok ? result.data : null;
  const state = resolveState(result, status ? 1 : 0);
  const buckets = status
    ? ([
        ['models_total', status.models_total],
        ['models_validated', status.models_validated],
        ['models_partial', status.models_partial],
        ['models_drift', status.models_drift],
        ['models_unvalidated', status.models_unvalidated],
        ['models_deprecated', status.models_deprecated],
      ] as const)
    : [];

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={meta('title')}
      description={meta('description')}
      labels={labels}
      path={endpoint}
      state={state}
      total={status ? 1 : 0}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={stateDetail(endpoint, status ? 1 : 0)}
      input={<SlaughterhousePanel path={endpoint} buckets={buckets} />}
      output={
        <div className="flex flex-col gap-3">
          <p>
            <Badge tone="warn" density="cozy" dot>
              {registry('declaredBadge')}
            </Badge>
          </p>
          <RecordScene
            caption={meta('title')}
            entries={[
              ...buckets.map(([label, value]) => ({ label, value: number(value) })),
              { label: 'last_run', value: scalar(status?.last_run) },
              {
                label: 'recent_failures',
                value: number(status?.recent_failures?.length ?? 0),
              },
            ]}
          />
        </div>
      }
      summary={
        <ProvenanceBar
          modelVersion={null}
          calibration={
            buckets.length > 0
              ? buckets
                  .slice(1)
                  .map(([label, value]) => `${label}=${value}`)
                  .join(' آ· ')
              : null
          }
          confidence={null}
          run={scalar(status?.last_run) || null}
        />
      }
      notes={<p className="text-sm text-ink-soft">{registry('slaughterhouseNote')}</p>}
    />
  );
}

async function SlaughterhousePanel({
  path,
  buckets,
}: {
  path: string;
  buckets: readonly (readonly [string, number])[];
}) {
  const t = await getTranslations('hydroma.suite');
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-ink-soft">{t('slaughterhousePanel')}</p>
      <ul className="num flex flex-col gap-1 text-xs text-ink">
        {buckets.map(([label, value]) => (
          <li key={label} className="flex justify-between gap-2">
            <span className="text-ink-soft">{label}</span>
            <span>{number(value)}</span>
          </li>
        ))}
      </ul>
      <p className="num break-all text-xs text-ink-faint">{path}</p>
    </div>
  );
}
