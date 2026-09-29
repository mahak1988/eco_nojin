/**
 * The execution contracts of the HyDroMa scientific tools, as the gateway
 * actually publishes them.
 *
 * ## Why this file exists
 *
 * The plan's gap table (row 6) names 110 single-archetype scientific pages as
 * the defect, and T07 is the answer: a sticky input contract, an output scene,
 * a standing provenance bar and a re-run affordance. T07 claims every route
 * under `/hydroma/tools/`, so one module that resolves a tool id to its real
 * contract is what keeps sixty-odd pages from being sixty-odd hand-written
 * layouts — and, more importantly, what keeps all of them agreeing about what
 * the gateway can and cannot return.
 *
 * ## The honesty rule this module encodes
 *
 * `engine/hydroma/mrv/metrics.py` sets the standard: a value is `real`,
 * `simulated` or `no_data`, and a simulated input downgrades the aggregate
 * even when the caller declared it real. The same discipline applies to the
 * metadata around a run. A response that does not carry a model version, a
 * calibration or a confidence interval cannot have one shown for it, so
 * `PROVENANCE_FIELDS` names the four fields the T07 bar must display and
 * `readProvenance` reports each one as either the real value the response
 * carried or `null`. A `null` is rendered as an explicit "not yet available"
 * label, never as a plausible number.
 *
 * Nothing in this file invents a value, a range, or an identifier.
 */

import { SCIENTIFIC_TOOL_IDS } from '@/lib/domains/registry';

/* -------------------------------------------------------------------------- */
/*  Contract families                                                          */
/* -------------------------------------------------------------------------- */

/**
 * The eight `hydroma_*` engine routers. Each publishes the same three routes:
 * a list (`{"count", "models"}`), one tool's metadata, and a run.
 *
 * `rowsKey` is `models` for all eight, verified against each router's
 * `list_*_tools` return statement rather than inferred from the leaf name.
 */
export const HYDROMA_TOOL_DOMAINS = [
  'carbon',
  'climate',
  'economics',
  'indices',
  'mrv',
  'simulation',
  'soil',
  'water',
] as const;

export type HydromaToolDomain = (typeof HYDROMA_TOOL_DOMAINS)[number];

/** `/api/v1/hydroma/<domain>` — the catalogue, `{count, models}`. */
export function hydromaListEndpoint(domain: HydromaToolDomain): string {
  return `/api/v1/hydroma/${domain}`;
}

/** `/api/v1/hydroma/<domain>/<id>` — one tool's registered parameter spec. */
export function hydromaSpecEndpoint(domain: HydromaToolDomain, id: string): string {
  return `/api/v1/hydroma/${domain}/${encodeURIComponent(id)}`;
}

/** `/api/v1/hydroma/<domain>/<id>/run` — the execution contract. */
export function hydromaRunEndpoint(domain: HydromaToolDomain, id: string): string {
  return `/api/v1/hydroma/${domain}/${encodeURIComponent(id)}/run`;
}

/**
 * The five scientific motors published by `services/api_gateway/routers/motors.py`.
 *
 * Read from `GET /motors/list`, not restated: a motor added there and not here
 * would render as "unknown tool" instead of as a working instrument, which is
 * the failure mode a duplicated id list invites.
 */
export const MOTOR_LIST_ENDPOINT = '/motors/list';
export const MOTOR_RUN_ENDPOINT = '/motors/run';
export const MOTOR_STATUS_ENDPOINT = (runId: string): string =>
  `/motors/status/${encodeURIComponent(runId)}`;

/** `/api/v1/models` — the twenty-two fidelity-labelled scientific models. */
export const MODEL_LIST_ENDPOINT = '/api/v1/models';
export const MODEL_SPEC_ENDPOINT = (slug: string): string =>
  `/api/v1/models/${encodeURIComponent(slug)}`;
export const MODEL_RUN_ENDPOINT = (slug: string): string =>
  `/api/v1/models/${encodeURIComponent(slug)}/run`;

/* -------------------------------------------------------------------------- */
/*  The registry (catalogue) read                                             */
/* -------------------------------------------------------------------------- */

/**
 * `GET /api/v1/tool-registry/{tool_id}` — the catalogue entry.
 *
 * Read best-effort. The table is empty on a fresh database and the route is a
 * catalogue, not an execution contract, so a 404 here never makes a tool
 * unavailable — it only means the name and reference fall back to the engine's
 * own metadata.
 */
export const TOOL_REGISTRY_ENDPOINT = (toolId: string): string =>
  `/api/v1/tool-registry/${encodeURIComponent(toolId)}`;

export interface ToolRegistryRecord {
  tool_id: string;
  name_fa: string | null;
  name_en: string | null;
  domain: string | null;
  category: string | null;
  fidelity: string | null;
  reference: string | null;
  description: string | null;
  formula: string | null;
  service_slug: string | null;
  endpoint_path: string | null;
  phase: number | null;
  is_active: boolean;
}

/* -------------------------------------------------------------------------- */
/*  The registered parameter contract                                         */
/* -------------------------------------------------------------------------- */

export type ToolParamKind = 'float' | 'int' | 'str' | 'select' | 'list_float' | 'list_str';

export interface ToolParamSpec {
  name: string;
  label: string;
  unit: string;
  kind: ToolParamKind;
  default?: number | string | null;
  /** Absent defaults (`null`) mean the caller must supply the value. */
  optional?: boolean;
  options?: readonly string[];
  description?: string | null;
}

export interface ToolSpec {
  id: string;
  name_en?: string;
  description?: string;
  reference?: string;
  fidelity?: string;
  validity?: string;
  limitations?: string;
  /**
   * The input *data* a motor consumes, as `GET /motors/list` names them.
   *
   * Distinct from `params`: a motor's parameters are the scenario it runs in,
   * while this is the data the model needs and which the platform fetches.
   */
  inputData?: readonly string[];
  params: ToolParamSpec[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

const PARAM_KINDS: readonly ToolParamKind[] = [
  'float',
  'int',
  'str',
  'select',
  'list_float',
  'list_str',
];

function toParam(value: unknown): ToolParamSpec | null {
  if (!isRecord(value)) return null;
  const name = typeof value.name === 'string' ? value.name : null;
  if (name === null) return null;
  const kind = PARAM_KINDS.includes(value.kind as ToolParamKind)
    ? (value.kind as ToolParamKind)
    : 'str';
  const rawDefault = value.default;
  const defaultValue =
    typeof rawDefault === 'number' || typeof rawDefault === 'string' ? rawDefault : null;
  const options = Array.isArray(value.options)
    ? value.options.filter((option): option is string => typeof option === 'string')
    : undefined;
  return {
    name,
    label: typeof value.label === 'string' ? value.label : name,
    unit: typeof value.unit === 'string' ? value.unit : '',
    kind,
    default: defaultValue,
    optional: value.optional === true,
    options: options && options.length > 0 ? options : undefined,
    description: typeof value.description === 'string' ? value.description : null,
  };
}

/**
 * Parse a metadata response into a `ToolSpec`, or `null` when the shape is not
 * a registered parameter contract.
 *
 * A bare array is rejected on purpose: a response that is the array itself
 * carries no metadata beside it, so the input panel would have to invent its
 * own fields.
 */
export function parseToolSpec(value: unknown): ToolSpec | null {
  if (!isRecord(value)) return null;
  const id = typeof value.id === 'string' ? value.id : null;
  if (id === null) return null;
  const params = Array.isArray(value.params)
    ? value.params.map(toParam).filter((param): param is ToolParamSpec => param !== null)
    : [];
  return {
    id,
    name_en: typeof value.name_en === 'string' ? value.name_en : undefined,
    description: typeof value.description === 'string' ? value.description : undefined,
    reference: typeof value.reference === 'string' ? value.reference : undefined,
    fidelity: typeof value.fidelity === 'string' ? value.fidelity : undefined,
    validity: typeof value.validity === 'string' ? value.validity : undefined,
    limitations: typeof value.limitations === 'string' ? value.limitations : undefined,
    params,
  };
}

/** A spec param needs a value when the gateway gives it no usable default. */
export function isRequired(param: ToolParamSpec): boolean {
  if (param.optional === true) return false;
  return param.default === null || param.default === undefined;
}

/* -------------------------------------------------------------------------- */
/*  Resolving a tool id to a contract                                          */
/* -------------------------------------------------------------------------- */

export type ToolContract =
  | {
      kind: 'hydroma';
      toolId: string;
      domain: HydromaToolDomain;
      /** Where the parameter contract is read from. */
      specEndpoint: string;
      runEndpoint: string;
      /** The engine module the router dispatches to. */
      engine: string;
    }
  | {
      kind: 'model';
      toolId: string;
      specEndpoint: string;
      runEndpoint: string;
      engine: string;
    }
  | {
      kind: 'motor';
      toolId: string;
      specEndpoint: string;
      runEndpoint: string;
      engine: string;
    }
  | { kind: 'unknown'; toolId: string };

/**
 * The hydroma tool ids, keyed by domain.
 *
 * Thirty-five, counted from the eight routers' `_SPECS` at the time of writing.
 * This is a cache of *route shapes*, not a second source of truth for the
 * science: a tool id that is not in here simply resolves as `unknown` and the
 * page reports that no execution contract is published for it. An id that is in
 * here but has since been renamed fails loudly on the metadata fetch rather
 * than rendering an empty instrument.
 */
const HYDROMA_TOOL_IDS: Record<HydromaToolDomain, readonly string[]> = {
  carbon: ['carbon-calculator'],
  climate: ['et-fao56', 'irrigation-scheduler', 'weather-source'],
  economics: [
    'econ-analysis',
    'econ-costing',
    'econ-revenue',
    'econ-roi',
    'econ-employment',
    'econ-risk',
  ],
  soil: [
    'soil-texture',
    'soil-taxonomy',
    'soil-water-retention',
    'pedotransfer',
    'soil-physics',
    'soil-chemistry',
    'soil-salinity',
    'soil-health',
    'soil-recommendations',
  ],
  water: ['runoff-model', 'runoff-surface', 'groundwater-model', 'groundwater-service'],
  simulation: ['sim-calibration', 'sim-scenarios'],
  indices: ['ecsi', 'epia', 'esri', 'ewsi', 'hdvi', 'hlhs', 'hpheno', 'hyrue'],
  mrv: ['mrv-qa', 'mrv-metrics'],
};

/** The five motor keys published by `GET /motors/list`. */
const MOTOR_IDS: readonly string[] = ['swat_plus', 'aquacrop', 'rothc', 'hecras', 'what_if'];

/**
 * The twenty-two model slugs in `services/models/registry.py`.
 *
 * Also a cache of route shapes. A slug that leaves the registry makes its page
 * report "unknown model" from the gateway's own 404 rather than a stale
 * instrument.
 */
const MODEL_IDS: readonly string[] = [
  'et0_hargreaves',
  'runoff_volume',
  'check_dam_design',
  'contour_trench_design',
  'half_moon_design',
  'crop_yield',
  'compare_crops',
  'climate_projection',
  'apply_climate_change',
  'biomass_aboveground',
  'biomass_belowground',
  'rothc_pools',
  'farquhar_photosynthesis',
  'quantum_efficiency',
  'carbon_sequestration',
  'soil_health_index',
  'soil_pedotransfer',
  'salinity_class',
  'leaching_requirement',
  'van_genuchten_theta',
  'soil_water_retention',
  'erosion_usle',
];

export function resolveToolContract(toolId: string): ToolContract {
  for (const domain of HYDROMA_TOOL_DOMAINS) {
    if (HYDROMA_TOOL_IDS[domain].includes(toolId)) {
      return {
        kind: 'hydroma',
        toolId,
        domain,
        specEndpoint: hydromaSpecEndpoint(domain, toolId),
        runEndpoint: hydromaRunEndpoint(domain, toolId),
        engine: `services/api_gateway/routers/hydroma_${domain}.py`,
      };
    }
  }
  if (MOTOR_IDS.includes(toolId)) {
    return {
      kind: 'motor',
      toolId,
      specEndpoint: MOTOR_LIST_ENDPOINT,
      runEndpoint: MOTOR_RUN_ENDPOINT,
      engine: 'services/api_gateway/routers/motors.py',
    };
  }
  if (MODEL_IDS.includes(toolId)) {
    return {
      kind: 'model',
      toolId,
      specEndpoint: MODEL_SPEC_ENDPOINT(toolId),
      runEndpoint: MODEL_RUN_ENDPOINT(toolId),
      engine: 'services/models/registry.py',
    };
  }
  return { kind: 'unknown', toolId };
}

/** Every tool id with a real execution contract, for `generateStaticParams`. */
export function executableToolIds(): readonly string[] {
  return [
    ...HYDROMA_TOOL_DOMAINS.flatMap((domain) => HYDROMA_TOOL_IDS[domain]),
    ...MODEL_IDS,
    ...MOTOR_IDS,
  ];
}

/**
 * Declared catalogue ids that no router serves.
 *
 * Computed from `SCIENTIFIC_TOOL_IDS` rather than restated, so an id added to
 * the declared catalogue and routed later stops being reported as a gap on its
 * own. Thirty-eight of the fifty-one declared tools have no published
 * execution contract: the engine module exists and no gateway route invokes
 * it. The page names that gap instead of rendering an instrument it cannot run,
 * which is what §7 requires of a number that is not there.
 */
export const CATALOGUE_ONLY_TOOL_IDS: readonly string[] = SCIENTIFIC_TOOL_IDS.filter(
  (id: string) => resolveToolContract(id).kind === 'unknown',
);

/* -------------------------------------------------------------------------- */
/*  The motor input contract                                                   */
/* -------------------------------------------------------------------------- */

/**
 * `MotorRunRequest` transcribed from
 * `services/api_gateway/routers/motors.py`, field for field.
 *
 * The motor route publishes no parameter spec of its own — `GET /motors/list`
 * names the input *data* and nothing else — so the pydantic request model is
 * the only published statement of what a motor run takes. Transcribing it here
 * is reading the contract, not extending it: field name, kind, default and
 * range all come from that class.
 */
const MOTOR_PARAMS: readonly ToolParamSpec[] = [
  { name: 'motor_type', label: 'Motor', unit: '', kind: 'select', default: null },
  { name: 'scenario_name', label: 'Scenario', unit: '', kind: 'str', default: 'baseline' },
  {
    name: 'start_date',
    label: 'Start date',
    unit: 'YYYY-MM-DD',
    kind: 'str',
    default: '2026-01-01',
  },
  { name: 'end_date', label: 'End date', unit: 'YYYY-MM-DD', kind: 'str', default: '2026-12-31' },
  {
    name: 'time_step',
    label: 'Time step',
    unit: '',
    kind: 'select',
    default: 'daily',
    options: ['daily', 'monthly', 'event', 'static'],
  },
  {
    name: 'region_bounds',
    label: 'Region bounds',
    unit: 'minx,miny,maxx,maxy',
    kind: 'list_float',
    default: '51.0,35.0,51.05,35.05',
  },
  { name: 'crop', label: 'Crop', unit: '', kind: 'str', default: 'wheat', optional: true },
];

/** Build the motor's parameter contract from its `/motors/list` entry. */
export function motorSpec(
  motorId: string,
  name: string,
  description: string,
  inputData: readonly string[],
): ToolSpec {
  return {
    id: motorId,
    name_en: name,
    description,
    inputData,
    params: MOTOR_PARAMS.map((param) =>
      param.name === 'motor_type'
        ? { ...param, default: motorId, options: MOTOR_IDS }
        : { ...param },
    ),
  };
}

/* -------------------------------------------------------------------------- */
/*  Input validation                                                           */
/* -------------------------------------------------------------------------- */

export interface ToolInputError {
  name: string;
  reason: 'required' | 'not-a-number' | 'not-an-integer' | 'option';
}

/**
 * Validate query-string values against the registered parameter contract.
 *
 * This mirrors the gateway's own `build_kwargs` (optional and empty are
 * dropped; otherwise the declared default is used; anything left without a
 * value is a hard error) rather than inventing a second set of rules, so the
 * page refuses exactly what the gateway would refuse.
 */
export function validateToolInputs(
  spec: ToolSpec,
  search: Record<string, string | string[] | undefined>,
): { values: Record<string, string | number>; errors: ToolInputError[]; supplied: Set<string> } {
  const values: Record<string, string | number> = {};
  const errors: ToolInputError[] = [];
  const supplied = new Set<string>();

  for (const param of spec.params) {
    const raw = search[param.name];
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (value !== undefined) supplied.add(param.name);
    const trimmed = value?.trim() ?? '';

    if (trimmed === '') {
      if (param.default !== null && param.default !== undefined) {
        values[param.name] = param.default;
        continue;
      }
      if (param.optional === true) continue;
      errors.push({ name: param.name, reason: 'required' });
      continue;
    }

    if (param.kind === 'float' || param.kind === 'list_float') {
      const parts = param.kind === 'list_float' ? trimmed.split(/[;,]/) : [trimmed];
      const numbers: number[] = [];
      let numeric = true;
      for (const part of parts) {
        const parsed = Number(part.trim());
        if (!Number.isFinite(parsed)) numeric = false;
        else numbers.push(parsed);
      }
      if (!numeric) {
        errors.push({ name: param.name, reason: 'not-a-number' });
        continue;
      }
      values[param.name] = param.kind === 'list_float' ? numbers.join(',') : numbers[0];
      continue;
    }

    if (param.kind === 'int') {
      const parsed = Number(trimmed);
      if (!Number.isInteger(parsed)) {
        errors.push({ name: param.name, reason: 'not-an-integer' });
        continue;
      }
      values[param.name] = parsed;
      continue;
    }

    if (param.kind === 'select' && param.options && !param.options.includes(trimmed)) {
      errors.push({ name: param.name, reason: 'option' });
      continue;
    }

    values[param.name] = trimmed;
  }

  return { values, errors, supplied };
}

/** The query string that reproduces a run, in the spec's declared order. */
export function permalinkQuery(values: Record<string, string | number>): string {
  const search = new URLSearchParams();
  for (const [name, value] of Object.entries(values)) {
    if (value === '' || value === undefined || value === null) continue;
    search.set(name, String(value));
  }
  const query = search.toString();
  return query === '' ? '' : `?${query}`;
}

/* -------------------------------------------------------------------------- */
/*  The run                                                                   */
/* -------------------------------------------------------------------------- */

export interface ToolRunOutcome {
  ok: boolean;
  /** `0` when the request never reached the gateway. */
  status: number;
  /** The response body, or the failure detail. */
  body: unknown;
}

/**
 * Execute the contract.
 *
 * A motor run is asynchronous: `POST /motors/run` returns immediately with a
 * `run_id` and the result is collected by a background task, so the status
 * route is polled a bounded number of times. The bound is deliberate — a page
 * render that waits forever is worse than one that says the run is still going.
 */
export async function runTool(
  contract: ToolContract,
  values: Record<string, string | number>,
  init?: { signal?: AbortSignal },
): Promise<ToolRunOutcome> {
  if (contract.kind === 'unknown') {
    return { ok: false, status: 0, body: null };
  }

  if (contract.kind === 'motor') {
    return runMotor(values, init);
  }

  try {
    const response = await fetch(contract.runEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(values),
      cache: 'no-store',
      signal: init?.signal,
    });
    const text = await response.text();
    return {
      ok: response.ok,
      status: response.status,
      body: safeParse(text),
    };
  } catch (error) {
    return { ok: false, status: 0, body: error instanceof Error ? error.message : String(error) };
  }
}

const MOTOR_POLL_ATTEMPTS = 6;
const MOTOR_POLL_INTERVAL_MS = 700;

async function runMotor(
  values: Record<string, string | number>,
  init?: { signal?: AbortSignal },
): Promise<ToolRunOutcome> {
  const asText = (key: string, fallback: string): string =>
    typeof values[key] === 'string' ? (values[key] as string) : fallback;

  const body: Record<string, unknown> = {
    motor_type: asText('motor_type', ''),
    scenario_name: asText('scenario_name', 'baseline'),
    start_date: asText('start_date', '2026-01-01'),
    end_date: asText('end_date', '2026-12-31'),
    time_step: asText('time_step', 'daily'),
  };
  const bounds = String(values.region_bounds ?? '')
    .split(/[;,]/)
    .map((part) => Number(part.trim()))
    .filter((value) => Number.isFinite(value));
  if (bounds.length === 4) body.region_bounds = bounds;
  else body.region_bounds = [51.0, 35.0, 51.05, 35.05];
  if (typeof values.crop === 'string') body.parameters = { crop: values.crop };

  let started: Response;
  try {
    started = await fetch(MOTOR_RUN_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
      signal: init?.signal,
    });
  } catch (error) {
    return { ok: false, status: 0, body: error instanceof Error ? error.message : String(error) };
  }

  const startBody = safeParse(await started.text());
  if (!started.ok) return { ok: false, status: started.status, body: startBody };
  const runId =
    isRecord(startBody) && typeof startBody.run_id === 'string' ? startBody.run_id : null;
  if (runId === null) return { ok: false, status: started.status, body: startBody };

  for (let attempt = 0; attempt < MOTOR_POLL_ATTEMPTS; attempt += 1) {
    await delay(MOTOR_POLL_INTERVAL_MS, init?.signal);
    try {
      const statusResponse = await fetch(MOTOR_STATUS_ENDPOINT(runId), {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
        signal: init?.signal,
      });
      const statusBody = safeParse(await statusResponse.text());
      if (!statusResponse.ok) return { ok: false, status: statusResponse.status, body: statusBody };
      const status = isRecord(statusBody) ? statusBody.status : null;
      if (status === 'running') continue;
      return { ok: status !== 'failed', status: statusResponse.status, body: statusBody };
    } catch (error) {
      return {
        ok: false,
        status: 0,
        body: error instanceof Error ? error.message : String(error),
      };
    }
  }
  return { ok: true, status: 202, body: { run_id: runId, status: 'running' } };
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener('abort', () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

function safeParse(text: string): unknown {
  if (text === '') return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/* -------------------------------------------------------------------------- */
/*  The T07 provenance bar                                                     */
/* -------------------------------------------------------------------------- */

/**
 * The four cells of the bar, in the order §7 names them: model version,
 * calibration, confidence interval, run identifier.
 */
export const PROVENANCE_FIELDS = [
  'modelVersion',
  'calibration',
  'confidenceInterval',
  'runId',
] as const;

export type ProvenanceField = (typeof PROVENANCE_FIELDS)[number];

export type ProvenanceValue = string | number | null;

/**
 * Read the bar's four fields out of a run response.
 *
 * Each is a `null` unless the response literally carried it. A `null` renders
 * as the explicit "not yet available" label and is counted in
 * `provenanceGaps`, so a page states which field its contract omits rather than
 * showing a plausible stand-in.
 */
export function readProvenance(body: unknown): Record<ProvenanceField, ProvenanceValue> {
  const empty: Record<ProvenanceField, ProvenanceValue> = {
    modelVersion: null,
    calibration: null,
    confidenceInterval: null,
    runId: null,
  };
  if (!isRecord(body)) return empty;

  const version =
    firstString(body, ['model_version', 'version', 'engine_version']) ??
    (isRecord(body.inputs) ? firstString(body.inputs, ['model_version', 'version']) : null);
  const calibration = isRecord(body.calibration) ? summariseCalibration(body.calibration) : null;
  const confidence = firstString(body, [
    'confidence_interval',
    'confidenceInterval',
    'ci95',
    'ci_95',
  ]);
  // `id` is deliberately not a candidate. The hydroma routers answer a run with
  // `{"id", "result"}`, where `id` is the *model* the reader asked for and not an
  // identifier of the run; printing it in the run-identifier cell would put a
  // model name where a run record belongs, which is the kind of substitution the
  // bar exists to prevent.
  const runId = firstString(body, ['run_id', 'chain_id']);

  return {
    modelVersion: version,
    calibration,
    confidenceInterval: confidence,
    runId,
  };
}

function firstString(source: Record<string, unknown>, keys: readonly string[]): string | null {
  for (const key of keys) {
    const value = source[key];
    if (typeof value === 'string' && value.trim() !== '') return value;
    if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  }
  return null;
}

/**
 * `/motors/chain` is the only contract that returns a calibration block, and
 * only a real one when observed values were supplied. An absent or unsuccessful
 * block is summarised as its own status rather than as a number.
 */
function summariseCalibration(block: Record<string, unknown>): string {
  const status = typeof block.status === 'string' ? block.status : null;
  if (status === 'ok') {
    const value = block.kge;
    const variable = block.variable;
    if (typeof value === 'number' && typeof variable === 'string') {
      return `KGE ${value} on {${variable}}`;
    }
    if (typeof value === 'number') return `KGE ${value}`;
    return 'ok';
  }
  return status ?? 'not yet available';
}

/** Which of the four cells the response could not fill. */
export function provenanceGaps(
  provenance: Record<ProvenanceField, ProvenanceValue>,
): readonly ProvenanceField[] {
  return PROVENANCE_FIELDS.filter((field) => provenance[field] === null);
}
