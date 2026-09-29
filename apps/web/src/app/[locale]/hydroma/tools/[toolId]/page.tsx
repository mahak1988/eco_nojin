import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';

import { InstrumentPage } from '@/components/templates/InstrumentPage';
import { Badge } from '@/components/ui/Badge';
import type { DataState } from '@/components/ui/StateSlot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { apiGet } from '@/lib/api/client';
import type { TemplateLabels } from '@/lib/design/page-templates';
import { getScientificTool } from '@/lib/domains/registry';

import {
  CATALOGUE_ONLY_TOOL_IDS,
  executableToolIds,
  isRequired,
  motorSpec,
  PROVENANCE_FIELDS,
  type ProvenanceField,
  parseToolSpec,
  permalinkQuery,
  provenanceGaps,
  readProvenance,
  resolveToolContract,
  runTool,
  TOOL_REGISTRY_ENDPOINT,
  type ToolContract,
  type ToolInputError,
  type ToolParamSpec,
  type ToolRegistryRecord,
  type ToolRunOutcome,
  type ToolSpec,
  validateToolInputs,
} from '../contracts';

const PROVENANCE_LABEL_KEYS: Record<ProvenanceField, string> = {
  modelVersion: 'tools.field.modelVersion',
  calibration: 'tools.field.calibration',
  confidenceInterval: 'tools.field.confidenceInterval',
  runId: 'tools.field.runId',
};

/**
 * Written out rather than built from the failure reason, so a new reason cannot
 * reach a key that does not exist: a missing key is a `MISSING_MESSAGE` at
 * request time, which renders as an empty 200 rather than as an error.
 */
const INVALID_LABEL_KEYS: Record<ToolInputError['reason'], string> = {
  required: 'input.invalid.required',
  'not-a-number': 'input.invalid.not-a-number',
  'not-an-integer': 'input.invalid.not-an-integer',
  option: 'input.invalid.option',
};

type DataSource = 'real' | 'simulated' | 'no_data';

const SOURCE_LABEL_KEYS: Record<DataSource, string> = {
  real: 'notes.source.real',
  simulated: 'notes.source.simulated',
  no_data: 'notes.source.no_data',
};

/**
 * How many rows of a run response the output scene shows.
 *
 * A model that returns a daily series has thousands, and a table of four thousand
 * is not an output scene. The cap is disclosed on the page rather than applied
 * silently: a truncated answer that says so is a partial answer, and one that does
 * not is the failure `StateSlot`'s `partial` state exists to prevent.
 */
const OUTPUT_ROW_LIMIT = 40;

/**
 * Every string the surface renders, already resolved through `getTranslations`.
 *
 * Resolved here rather than passed as a translator so the sub-components below
 * are ordinary presentational functions with no locale knowledge of their own —
 * the same shape `EndpointForm` and `ScientificToolLayout` already use, and the
 * reason a copy string cannot drift out of the catalogue from a nested closure.
 */
interface Copy {
  invalid: Record<ToolInputError['reason'], string>;
  provenanceField: Record<ProvenanceField, string>;
  source: Record<DataSource, string>;
  run: string;
  fixErrors: string;
  required: string;
  optional: string;
  pickOne: string;
  noParameters: string;
  contractUnavailable: string;
  noContract: string;
  noContractDeclared: string;
  noContractUnknown: string;
  outputField: string;
  outputValue: string;
  outputEmpty: string;
  outputNone: string;
  outputBlocked: string;
  outputTruncated: string;
  notAvailable: string;
  fidelity: string;
  reference: string;
  engine: string;
  execution: string;
  barMissing: string;
  noReference: string;
  validity: string;
  limitations: string;
  inputData: string;
  detailNoContract: string;
  integrity: string;
  noBadge: string;
  rerun: string;
  back: string;
}

/** Every tool id with a published execution contract, enumerated ahead of time. */
export function generateStaticParams() {
  return executableToolIds().map((toolId: string) => ({ toolId }));
}

export const dynamicParams = true;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; toolId: string }>;
}): Promise<Metadata> {
  const { locale, toolId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('tools');
  const record = await apiGet<ToolRegistryRecord>(TOOL_REGISTRY_ENDPOINT(toolId));
  const name =
    (record.ok ? (locale === 'fa' ? record.data.name_fa : record.data.name_en) : null) ?? toolId;
  return {
    title: `${name} · ${t('meta.title')}`,
    description: t('meta.description'),
    robots: { index: false, follow: true },
    alternates: {
      canonical: canonicalFor(locale, `/hydroma/tools/${toolId}`),
      languages: languageAlternates(`/hydroma/tools/${toolId}`),
    },
  };
}

/**
 * T07 — the scientific instrument.
 *
 * One page serves every tool under `/hydroma/tools/`, which is the point rather
 * than a shortcut: sixty-odd pages that share one archetype are only maintainable
 * while they share one implementation, and the plan's gap table row 6 is a
 * complaint about sixty-odd pages that shared a *list* layout. What makes this an
 * instrument rather than a list is the four things below, and none is optional:
 *
 *   1. the registered input contract, rendered as a real form, in the `prelude`
 *      slot — so it survives a failed run, which is when the parameters matter;
 *   2. an output scene that renders the contract's own response and nothing else;
 *   3. a standing provenance bar whose four cells are read from the response or
 *      declared absent, never filled with a plausible number;
 *   4. a permalink carrying every value the run used, so "run again with these
 *      inputs" is a link rather than a re-typed form.
 */
export default async function ScientificToolPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; toolId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale, toolId } = await params;
  const search = await searchParams;
  setRequestLocale(locale);
  const t = await getTranslations('tools');

  const contract = resolveToolContract(toolId);
  const declared = getScientificTool(toolId);

  const [registry, specResult] = await Promise.all([
    apiGet<ToolRegistryRecord>(TOOL_REGISTRY_ENDPOINT(toolId)),
    loadSpec(contract),
  ]);

  // Nothing declares this id, no execution contract resolves it, and the
  // catalogue does not list it: there is no page to render. Inventing one is how
  // a single-archetype scientific surface appeared in the first place.
  if (contract.kind === 'unknown' && !declared && !registry.ok) notFound();

  const spec = specResult.spec;
  const validated = spec === null ? null : validateToolInputs(spec, search);
  const errors: ToolInputError[] = validated?.errors ?? [];
  const values = validated?.values ?? {};
  const supplied = validated?.supplied ?? new Set<string>();

  // A model is never run on page load. The first render shows the contract; a run
  // happens when the reader submits the form, and then the URL *is* the run.
  const runRequested = Object.keys(search).length > 0;
  const run =
    runRequested && contract.kind !== 'unknown' && errors.length === 0
      ? await runTool(contract, values)
      : null;

  const provenance = readProvenance(run?.body ?? null);
  const gaps = provenanceGaps(provenance);
  const state = resolveState({ contract, specResult, run, runRequested, errors });

  const copy: Copy = {
    invalid: {
      required: t(INVALID_LABEL_KEYS.required),
      'not-a-number': t(INVALID_LABEL_KEYS['not-a-number']),
      'not-an-integer': t(INVALID_LABEL_KEYS['not-an-integer']),
      option: t(INVALID_LABEL_KEYS.option),
    },
    provenanceField: {
      modelVersion: t(PROVENANCE_LABEL_KEYS.modelVersion),
      calibration: t(PROVENANCE_LABEL_KEYS.calibration),
      confidenceInterval: t(PROVENANCE_LABEL_KEYS.confidenceInterval),
      runId: t(PROVENANCE_LABEL_KEYS.runId),
    },
    source: {
      real: t(SOURCE_LABEL_KEYS.real),
      simulated: t(SOURCE_LABEL_KEYS.simulated),
      no_data: t(SOURCE_LABEL_KEYS.no_data),
    },
    run: t('input.run'),
    fixErrors: t('input.fixErrors'),
    required: t('input.required'),
    optional: t('input.optional'),
    pickOne: t('input.pickOne'),
    noParameters: t('input.noParameters'),
    contractUnavailable: t('input.contractUnavailable'),
    noContract: t('input.noContract'),
    noContractDeclared: t('input.noContractDeclared'),
    noContractUnknown: t('input.noContractUnknown'),
    outputField: t('output.field'),
    outputValue: t('output.value'),
    outputEmpty: t('output.empty'),
    outputNone: t('output.none'),
    outputBlocked: t('output.blocked', { count: errors.length }),
    outputTruncated: t('output.truncated', { count: OUTPUT_ROW_LIMIT }),
    notAvailable: t('field.notAvailable'),
    fidelity: t('field.fidelity'),
    reference: t('field.reference'),
    engine: t('field.engine'),
    execution: t('field.execution'),
    barMissing: t('bar.missing', { count: gaps.length }),
    noReference: t('detail.noReference'),
    validity: t('detail.validity'),
    limitations: t('detail.limitations'),
    inputData: t('detail.inputData'),
    detailNoContract: t('detail.noContract'),
    integrity: t('notes.integrity'),
    noBadge: t('notes.noBadge'),
    rerun: t('actions.rerun'),
    back: t('actions.back'),
  };

  const labels: TemplateLabels = {
    loading: t('states.loading'),
    empty: t('states.empty'),
    error: t('states.error'),
    partial: t('states.partial'),
    offline: t('states.offline'),
    action: t('states.retry'),
    provenance: t('provenance'),
    live: t('live'),
    unavailable: t('unavailable'),
    primaryAction: copy.run,
    footer: t('footer'),
    regions: {
      filters: t('regions.filters'),
      data: t('regions.data'),
      state: t('regions.state'),
      summary: t('regions.summary'),
      detail: t('regions.detail'),
      notes: t('regions.notes'),
      actions: t('regions.actions'),
      provenance: t('regions.provenance'),
      footer: t('regions.footer'),
    },
  };

  const record = registry.ok ? registry.data : null;
  const regions = { filters: labels.regions.filters, data: labels.regions.data };

  return (
    <InstrumentPage
      path={contract.kind === 'unknown' ? TOOL_REGISTRY_ENDPOINT(toolId) : contract.runEndpoint}
      state={state}
      total={spec?.params.length ?? 0}
      ok={spec !== null}
      title={titleOf(record, spec, toolId, locale)}
      description={spec?.description ?? record?.description ?? undefined}
      labels={labels}
      input={
        <InputPanel
          toolId={toolId}
          locale={locale}
          contract={contract}
          spec={spec}
          errors={errors}
          supplied={supplied}
          copy={copy}
        />
      }
      output={<OutputScene run={run} errorCount={errors.length} copy={copy} regions={regions} />}
      summary={<ProvenanceBar provenance={provenance} gaps={gaps} spec={spec} copy={copy} />}
      detail={<MethodNote contract={contract} spec={spec} record={record} copy={copy} />}
      notes={<IntegrityNote run={run} copy={copy} />}
      actions={
        <RunAgain
          locale={locale}
          toolId={toolId}
          permalink={permalinkQuery(values)}
          ran={run !== null}
          copy={copy}
        />
      }
    />
  );
}

/* -------------------------------------------------------------------------- */
/*  Contract loading                                                           */
/* -------------------------------------------------------------------------- */

interface SpecResult {
  spec: ToolSpec | null;
  /** Separates "the gateway is unreachable" from "there is no such tool". */
  status: number;
}

/**
 * Read the registered parameter contract for whichever family the id resolved to.
 * The hydroma routers and the model registry publish the spec object directly; the
 * motor route publishes a list whose entries name the input data and not the
 * parameters, so the motor's contract comes from its own request schema.
 */
async function loadSpec(contract: ToolContract): Promise<SpecResult> {
  if (contract.kind === 'unknown') return { spec: null, status: 0 };

  if (contract.kind === 'motor') {
    const listed = await apiGet<{
      motors?: { type?: string; name?: string; description?: string; inputs?: string[] }[];
    }>(contract.specEndpoint);
    if (!listed.ok) return { spec: null, status: listed.status };
    const entry = (listed.data.motors ?? []).find(
      (motor: { type?: string; name?: string; description?: string; inputs?: string[] }) =>
        motor.type === contract.toolId,
    );
    if (entry === undefined) return { spec: null, status: 404 };
    return {
      spec: motorSpec(
        contract.toolId,
        entry.name ?? contract.toolId,
        entry.description ?? '',
        entry.inputs ?? [],
      ),
      status: listed.status,
    };
  }

  const response = await apiGet<unknown>(contract.specEndpoint);
  if (!response.ok) return { spec: null, status: response.status };
  return { spec: parseToolSpec(response.data), status: response.status };
}

/* -------------------------------------------------------------------------- */
/*  The five states of §4.5                                                    */
/* -------------------------------------------------------------------------- */

function resolveState({
  contract,
  specResult,
  run,
  runRequested,
  errors,
}: {
  contract: ToolContract;
  specResult: SpecResult;
  run: ToolRunOutcome | null;
  runRequested: boolean;
  errors: readonly ToolInputError[];
}): DataState {
  // A declared tool with no published execution contract is a partial surface:
  // the catalogue knows the engine module, the gateway serves no route for it.
  if (contract.kind === 'unknown') return 'partial';
  if (specResult.spec === null) return specResult.status === 0 ? 'offline' : 'error';
  if (errors.length > 0) return 'error';
  if (!runRequested || run === null) return 'empty';
  if (run.status === 0) return 'offline';
  if (!run.ok) return 'error';
  if (isDegraded(run.body)) return 'partial';
  return 'ready';
}

/**
 * A motor that finished but reports its own inputs as synthetic, or a chain that
 * completed only some stages, is a partial answer and is labelled as one rather
 * than rendered as a whole one.
 */
function isDegraded(body: unknown): boolean {
  if (typeof body !== 'object' || body === null) return false;
  const record = body as Record<string, unknown>;
  if (record.status === 'partial' || record.status === 'degraded') return true;
  const result = record.result;
  if (typeof result !== 'object' || result === null) return false;
  const inner = result as Record<string, unknown>;
  return inner.status === 'partial' || inner.status === 'degraded';
}

/**
 * The heading.
 *
 * The catalogue's own name is preferred because it is the one written in the
 * reader's language; the engine's `name_en` is the fallback so a tool still reads
 * as a tool when the registry table has no row for it, which is the normal state
 * of a freshly migrated database. The raw id is the last resort, and it is always
 * legible — a heading of `et0_hargreaves` is more honest than a heading of
 * nothing.
 */
function titleOf(
  record: ToolRegistryRecord | null,
  spec: ToolSpec | null,
  toolId: string,
  locale: string,
): string {
  if (record !== null) {
    const name =
      (locale === 'fa' ? record.name_fa : record.name_en) ?? record.name_fa ?? record.name_en;
    if (name) return name;
  }
  return spec?.name_en ?? toolId;
}

/* -------------------------------------------------------------------------- */
/*  1. The sticky input contract                                               */
/* -------------------------------------------------------------------------- */

function InputPanel({
  toolId,
  locale,
  contract,
  spec,
  errors,
  supplied,
  copy,
}: {
  toolId: string;
  locale: string;
  contract: ToolContract;
  spec: ToolSpec | null;
  errors: readonly ToolInputError[];
  supplied: Set<string>;
  copy: Copy;
}) {
  if (contract.kind === 'unknown') {
    return (
      <div className="space-y-2">
        <p className="text-sm text-ink">{copy.noContract}</p>
        <p className="text-sm text-ink-soft">
          {CATALOGUE_ONLY_TOOL_IDS.includes(toolId)
            ? copy.noContractDeclared
            : copy.noContractUnknown}
        </p>
        <p className="num text-xs text-ink-faint">
          {getScientificTool(toolId)?.sourceOfTruth ?? TOOL_REGISTRY_ENDPOINT(toolId)}
        </p>
      </div>
    );
  }

  if (spec === null) {
    return (
      <div className="space-y-2">
        <p className="text-sm text-ink">{copy.contractUnavailable}</p>
        <p className="num text-xs text-ink-faint">{contract.specEndpoint}</p>
      </div>
    );
  }

  const errorFor = (name: string): string | null => {
    const error = errors.find((candidate) => candidate.name === name);
    return error === undefined ? null : copy.invalid[error.reason];
  };

  return (
    <form method="get" action={`/${locale}/hydroma/tools/${toolId}`} className="space-y-3">
      {spec.params.length === 0 ? (
        <p className="text-sm text-ink-soft">{copy.noParameters}</p>
      ) : null}
      {spec.params.map((param: ToolParamSpec) => (
        <ParamField
          key={param.name}
          param={param}
          error={errorFor(param.name)}
          dirty={supplied.has(param.name)}
          copy={copy}
        />
      ))}
      <button type="submit" className="btn btn-primary w-full">
        {errors.length > 0 ? copy.fixErrors : copy.run}
      </button>
      <p className="num text-xs text-ink-faint">{contract.runEndpoint}</p>
    </form>
  );
}

/**
 * One registered parameter, as the contract declares it.
 *
 * The only validation offered is the contract's own: a field it marks required is
 * `required`, a field with a declared default is pre-filled with that default,
 * and a `select` offers exactly the options the contract lists. No range is
 * invented, because a plausible-looking bound the gateway never published is a
 * number the platform would be asserting about its own science.
 */
function ParamField({
  param,
  error,
  dirty,
  copy,
}: {
  param: ToolParamSpec;
  error: string | null;
  dirty: boolean;
  copy: Copy;
}) {
  const id = `param-${param.name}`;
  const required = isRequired(param);
  // `list_float` is text, not a number input: the contract takes a comma- or
  // semicolon-separated series, and a numeric input cannot express one.
  const decimal = param.kind === 'float';
  const declaredDefault =
    param.default === null || param.default === undefined ? undefined : String(param.default);

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-sm text-ink">{param.label}</span>
        <span className="num text-xs text-ink-faint">
          {param.unit === '' ? `«{param.name}»` : `«{param.name}» · ${param.unit}`}
        </span>
      </label>
      {param.kind === 'select' && param.options ? (
        <select
          id={id}
          name={param.name}
          required={required}
          defaultValue={declaredDefault ?? ''}
          aria-invalid={error !== null}
          aria-describedby={error === null ? undefined : `${id}-error`}
          className="w-full rounded border border-line-strong bg-surface px-3 py-2 text-sm text-ink"
        >
          {declaredDefault === undefined ? <option value="">{copy.pickOne}</option> : null}
          {param.options.map((option: string) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          name={param.name}
          type={decimal ? 'number' : 'text'}
          step={param.kind === 'int' ? '1' : decimal ? 'any' : undefined}
          required={required}
          defaultValue={declaredDefault}
          placeholder={param.name}
          aria-invalid={error !== null}
          aria-describedby={error === null ? undefined : `${id}-error`}
          data-dirty={dirty ? 'true' : undefined}
          className="w-full rounded border border-line-strong bg-surface px-3 py-2 text-sm text-ink"
        />
      )}
      <p className="text-xs text-ink-soft">
        {required ? copy.required : copy.optional}
        {param.description ? ` · ${param.description}` : ''}
      </p>
      {error === null ? null : (
        <p id={`${id}-error`} className="text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  2. The output scene                                                        */
/* -------------------------------------------------------------------------- */

function OutputScene({
  run,
  errorCount,
  copy,
  regions,
}: {
  run: ToolRunOutcome | null;
  errorCount: number;
  copy: Copy;
  // `TemplateRegion` takes `title?: string` and omits the heading when it is
  // absent, and `labels.regions` is a `Partial<Record<RequiredRegion, string>>`
  // because not every archetype declares every region. The tools fragment does
  // declare both of these, so the value is present at runtime; the prop type was
  // simply narrower than the data, and rendering the literal word `undefined` is
  // worse than rendering no heading.
  regions: Partial<{ filters: string; data: string }>;
}) {
  if (errorCount > 0) {
    return <p className="text-sm text-ink-soft">{copy.outputBlocked}</p>;
  }
  if (run === null) {
    return <p className="text-sm text-ink-soft">{copy.outputNone}</p>;
  }
  const rows = flattenResult(run.body);
  if (rows.length === 0) {
    return <p className="text-sm text-ink-soft">{copy.outputEmpty}</p>;
  }
  return (
    <div className="space-y-2">
      <table className="w-full border-collapse text-sm">
        {regions.data ? <caption className="sr-only">{regions.data}</caption> : null}
        <thead>
          <tr className="border-b border-line">
            <th scope="col" className="py-2 pe-3 text-start text-xs text-ink-soft">
              {copy.outputField}
            </th>
            <th scope="col" className="py-2 ps-3 text-start text-xs text-ink-soft">
              {copy.outputValue}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, OUTPUT_ROW_LIMIT).map((row) => (
            <tr key={row.key} className="border-b border-line align-top">
              <th scope="row" className="py-2 pe-3 text-start text-xs text-ink-soft">
                <span className="num">{row.key}</span>
              </th>
              <td className="py-2 ps-3 text-start text-ink">
                <span className="num break-words">{row.value}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length <= OUTPUT_ROW_LIMIT ? null : (
        <p className="text-xs text-ink-faint" data-truncated-rows={rows.length}>
          {copy.outputTruncated}
        </p>
      )}
    </div>
  );
}

/**
 * Flatten a run response into label/value rows.
 *
 * A result may be a scalar, a list, or a nested object. Scalars become rows and
 * array indices are kept so a reader can find a value inside a series; a long
 * string is truncated with an ellipsis rather than rendered whole. Nothing is
 * reordered, renamed, or rounded: the table shows the contract's own answer.
 */
function flattenResult(
  body: unknown,
  prefix = '',
  out: { key: string; value: string }[] = [],
): { key: string; value: string }[] {
  if (body === null || body === undefined) return out;
  if (Array.isArray(body)) {
    body.forEach((entry, index) => {
      flattenResult(entry, prefix === '' ? `[${index}]` : `${prefix}[${index}]`, out);
    });
    return out;
  }
  if (typeof body === 'object') {
    for (const [key, value] of Object.entries(body as Record<string, unknown>)) {
      flattenResult(value, prefix === '' ? key : `${prefix}.${key}`, out);
    }
    return out;
  }
  const text = String(body);
  out.push({ key: prefix, value: text.length > 400 ? `${text.slice(0, 400)}…` : text });
  return out;
}

/* -------------------------------------------------------------------------- */
/*  3. The standing provenance bar                                             */
/* -------------------------------------------------------------------------- */

/**
 * The bar §7 requires: model version, calibration, confidence interval, run
 * identifier — permanently visible, and empty where the contract is empty.
 *
 * A cell the response did not fill renders the explicit "not yet available" label
 * and is counted in the note underneath, so a reader can see which field the
 * contract omits instead of being shown a plausible stand-in. That is the point of
 * the bar: at present no execution contract in the gateway returns a model version
 * and none returns a confidence interval, and the bar is what makes that visible
 * on the page rather than in a code review.
 */
function ProvenanceBar({
  provenance,
  gaps,
  spec,
  copy,
}: {
  provenance: Record<ProvenanceField, string | number | null>;
  gaps: readonly ProvenanceField[];
  spec: ToolSpec | null;
  copy: Copy;
}) {
  return (
    <div className="flex flex-col gap-3">
      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {PROVENANCE_FIELDS.map((field: ProvenanceField) => {
          const value = provenance[field];
          return (
            <div key={field} className="min-w-0">
              <dt className="text-xs text-ink-soft">{copy.provenanceField[field]}</dt>
              <dd
                className={`num mt-1 break-words text-sm ${value === null ? 'text-ink-faint' : 'text-ink'}`}
                data-provenance-field={field}
              >
                {value === null ? copy.notAvailable : String(value)}
              </dd>
            </div>
          );
        })}
      </dl>
      {spec?.fidelity === undefined ? null : (
        <p className="text-xs text-ink-soft">
          <span className="text-ink-faint">{copy.fidelity}: </span>
          <span className="num text-ink">{spec.fidelity}</span>
        </p>
      )}
      {gaps.length === 0 ? null : (
        <p className="text-xs text-copper" data-provenance-gaps={gaps.join(',')}>
          {copy.barMissing}
        </p>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  4. How this works                                                          */
/* -------------------------------------------------------------------------- */

function MethodNote({
  contract,
  spec,
  record,
  copy,
}: {
  contract: ToolContract;
  spec: ToolSpec | null;
  record: ToolRegistryRecord | null;
  copy: Copy;
}) {
  const reference = spec?.reference ?? record?.reference ?? null;
  const engine =
    contract.kind === 'unknown'
      ? (getScientificTool(contract.toolId)?.sourceOfTruth ?? null)
      : contract.engine;
  return (
    <div className="space-y-2 text-sm">
      <p>
        <span className="text-ink-soft">{copy.reference}: </span>
        {reference === null ? (
          <span className="text-ink-faint">{copy.noReference}</span>
        ) : (
          <span className="text-ink">{reference}</span>
        )}
      </p>
      {spec?.validity === undefined ? null : (
        <p>
          <span className="text-ink-soft">{copy.validity}: </span>
          <span className="text-ink">{spec.validity}</span>
        </p>
      )}
      {spec?.limitations === undefined ? null : (
        <p>
          <span className="text-ink-soft">{copy.limitations}: </span>
          <span className="text-ink">{spec.limitations}</span>
        </p>
      )}
      {spec?.inputData === undefined || spec.inputData.length === 0 ? null : (
        <p>
          <span className="text-ink-soft">{copy.inputData}: </span>
          <span className="num text-ink">{spec.inputData.join('، ')}</span>
        </p>
      )}
      <p>
        <span className="text-ink-soft">{copy.engine}: </span>
        <span className="num text-ink-faint">{engine ?? copy.notAvailable}</span>
      </p>
      {contract.kind === 'unknown' ? (
        <p className="text-copper">{copy.detailNoContract}</p>
      ) : (
        <p className="num text-xs text-ink-faint">
          {copy.execution}: {contract.runEndpoint}
        </p>
      )}
      {record?.fidelity == null ? null : (
        <p>
          <Badge tone="neutral" density="dense">
            {copy.fidelity}: {record.fidelity}
          </Badge>
        </p>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  5. The integrity note                                                      */
/* -------------------------------------------------------------------------- */

/**
 * The engine's own provenance badge, repeated verbatim when the response carries
 * one.
 *
 * `engine/hydroma/mrv/metrics.py` is the standard the platform holds itself to: a
 * value is `real`, `simulated` or `no_data`, and a simulated input downgrades the
 * aggregate even when the caller declared it real. When a result carries that
 * badge, the page shows the badge and the warning the engine wrote. When it does
 * not, the page says so — which is the honest reading, since the absence of a
 * badge is not evidence that a value was measured.
 */
function IntegrityNote({ run, copy }: { run: ToolRunOutcome | null; copy: Copy }) {
  const badge = readBadge(run?.body ?? null);
  return (
    <div className="space-y-2 text-sm">
      <p className="text-ink-soft">{copy.integrity}</p>
      {badge === null ? (
        <p className="text-xs text-ink-faint">{copy.noBadge}</p>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={badge.source === 'simulated' ? 'warn' : 'neutral'} density="compact" dot>
            {copy.source[badge.source]}
          </Badge>
          {badge.warning === null ? null : (
            <span className="text-xs text-copper">{badge.warning}</span>
          )}
        </div>
      )}
    </div>
  );
}

function readBadge(body: unknown): { source: DataSource; warning: string | null } | null {
  if (typeof body !== 'object' || body === null) return null;
  const root = body as Record<string, unknown>;
  const result = root.result;
  const candidates: Record<string, unknown>[] = [root];
  if (typeof result === 'object' && result !== null) {
    const inner = result as Record<string, unknown>;
    candidates.unshift(inner);
    const metrics = inner.metrics;
    if (typeof metrics === 'object' && metrics !== null) {
      for (const value of Object.values(metrics as Record<string, unknown>)) {
        if (typeof value === 'object' && value !== null) {
          candidates.push(value as Record<string, unknown>);
        }
      }
    }
  }
  for (const candidate of candidates) {
    const source = candidate.data_source;
    if (source === 'real' || source === 'simulated' || source === 'no_data') {
      return {
        source,
        warning: typeof candidate.warning === 'string' ? candidate.warning : null,
      };
    }
  }
  return null;
}

/* -------------------------------------------------------------------------- */
/*  6. Run again with these inputs                                             */
/* -------------------------------------------------------------------------- */

/**
 * "Run again with these inputs" is a permalink, not a button.
 *
 * Every value the run actually used is in the query string, so a colleague who
 * opens the link reproduces the same numbers from the same contract. That is the
 * reproducibility the plan asks for, and it costs no client JavaScript.
 */
function RunAgain({
  locale,
  toolId,
  permalink,
  ran,
  copy,
}: {
  locale: string;
  toolId: string;
  permalink: string;
  ran: boolean;
  copy: Copy;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {ran ? (
        <Link href={`/${locale}/hydroma/tools/${toolId}${permalink}`} className="btn btn-ghost">
          {copy.rerun}
        </Link>
      ) : null}
      <Link href={`/${locale}/hydroma`} className="btn btn-ghost">
        {copy.back}
      </Link>
    </div>
  );
}
