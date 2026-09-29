import { getTranslations } from 'next-intl/server';

import type { DataState } from '@/components/ui/StateSlot';
import type { ApiResult } from '@/lib/api/client';
import type { TemplateLabels } from '@/lib/design/page-templates';

/**
 * Reading the HyDroMa contracts.
 *
 * Every helper here exists because a wrong answer to "what key is the array in"
 * or "what state is this page in" is invisible in review and catastrophic in the
 * browser: `ResourcePage` renders its *empty* state over a 200 when the field it
 * reads is absent, so a page shows a fabricated zero next to data that arrived.
 * So the two questions are answered once, here, from the router that serves the
 * response, and every page in this subtree asks the same helper.
 *
 * The contracts themselves are declared, never inferred from the route name:
 *
 *   hydroma_soil.py:428       `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_water.py:266      `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_indices.py:569    `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_mrv.py:141        `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_simulation.py:86  `return {"count": len(_SPECS), "models": _SPECS}`
 *   hydroma_dashboard.py:734  `return [ModelMeta(**m) for m in models]` — a bare
 *                             array, so there is no envelope key to name
 *   hydroma_ops.py:27         `return run_all()` → `{total, passed, failed,
 *                             pass_rate, checks: [...]}`
 *   validation/router.py:38   `{"checks": [...], "total": n}`
 */

/** A parameter as the six tool families declare it (`hydroma_*.py: _SPECS`). */
export interface SpecParam {
  name?: string;
  label?: string;
  unit?: string;
  kind?: string;
  default?: unknown;
  options?: unknown[];
  optional?: boolean;
}

/** One tool's metadata record. `hydroma_*.py: return spec`. */
export interface ToolSpec {
  id?: string;
  name_en?: string;
  description?: string;
  reference?: string;
  params?: SpecParam[];
  [key: string]: unknown;
}

/** The `{count, models}` envelope the six families share. */
export interface SpecEnvelope {
  count?: number;
  models?: ToolSpec[];
}

/** `hydroma_dashboard.py: ModelInput`. */
export interface ModelInput {
  name: string;
  description: string;
  type: string;
  unit?: string | null;
  required?: boolean;
  default?: unknown;
  minimum?: number | null;
  maximum?: number | null;
  enum?: unknown[] | null;
}

/** `hydroma_dashboard.py: ModelOutput`. */
export interface ModelOutput {
  name: string;
  description: string;
  type: string;
  unit?: string | null;
}

/** `hydroma_dashboard.py: BenchmarkData` — the only accuracy figure published. */
export interface BenchmarkData {
  backend: string;
  latency_ms?: number | null;
  memory_mb?: number | null;
  accuracy_score?: number | null;
  last_run?: string | null;
}

/** `hydroma_dashboard.py: ValidationStatus`. */
export interface ValidationStatus {
  status: string;
  message?: string | null;
  last_validated?: string | null;
}

/** `hydroma_dashboard.py: ModelMeta` / `ModelDetail`. */
export interface ModelMeta {
  id: string;
  name: string;
  category: string;
  description: string;
  version: string;
  language: string;
  reference: string;
  inputs?: ModelInput[];
  outputs?: ModelOutput[];
  validation?: ValidationStatus;
  performance?: BenchmarkData[];
  status: string;
  repo_path?: string;
  test_file?: string | null;
  test_cases?: Record<string, unknown>[];
  validation_history?: Record<string, unknown>[];
}

/** `hydroma_dashboard.py: ValidationReport`. */
export interface ValidationReport {
  model_id: string;
  overall_status: string;
  test_cases_total: number;
  test_cases_passed: number;
  test_cases_failed: number;
  test_cases_skipped: number;
  details: Record<string, unknown>[];
  generated_at: string;
}

/** `hydroma_dashboard.py: SlaughterhouseStatus`. */
export interface SlaughterhouseStatus {
  models_total: number;
  models_validated: number;
  models_partial: number;
  models_drift: number;
  models_unvalidated: number;
  models_deprecated: number;
  last_run: string | null;
  recent_failures?: Record<string, unknown>[];
}

/** `services/validation/formula_checks.py: CheckResult`. */
export interface CheckResult {
  id: string;
  label: string;
  kind: string;
  source?: string;
  expected?: number | string;
  actual?: number | string;
  tolerance?: number;
  unit?: string;
  passed: boolean;
  note?: string;
}

/** `services/validation/formula_checks.py: run_all()`. */
export interface SuiteReport {
  total?: number;
  passed?: number;
  failed?: number;
  pass_rate?: number;
  checks?: CheckResult[];
  error?: string;
}

/** Rows a table shows before the page declares itself `partial`. */
export const PREVIEW_LIMIT = 50;

/**
 * Read the array out of a response, or say there is none.
 *
 * A bare array is returned as itself, which is the case `/api/v1/hydroma/models`
 * and `/api/v1/hub/shared` are. Anything else needs the declared key, and an
 * absent key yields an empty array — which the caller turns into the `empty`
 * state naming the contract, never into a row set invented from the route name.
 */
export function readRows<T>(data: unknown, rowsKey?: string): T[] {
  if (Array.isArray(data)) return data as T[];
  if (!rowsKey || typeof data !== 'object' || data === null) return [];
  const value = (data as Record<string, unknown>)[rowsKey];
  return Array.isArray(value) ? (value as T[]) : [];
}

/**
 * The five states of §4.5, decided once.
 *
 * `status === 0` is a transport failure, not a server error: `apiGet` reports it
 * that way when `fetch` throws, which is what an offline reader sees. A page
 * that told an offline reader "the server is unavailable" would be the exact
 * failure §4.5 exists to prevent.
 */
export function resolveState<T>(result: ApiResult<T>, total: number): DataState {
  if (!result.ok) return result.status === 0 ? 'offline' : 'error';
  if (total === 0) return 'empty';
  return total > PREVIEW_LIMIT ? 'partial' : 'ready';
}

/** `path · count`, the same second line `ResourcePage` puts under the state. */
export function stateDetail(path: string, total: number): string {
  return `${path} · ${total}`;
}

/**
 * `TemplateLabels` for the twelve archetypes, resolved through the catalogue.
 *
 * The five states reuse the strings `ResourcePage.resourceLabels()` already
 * builds, so a state can say one thing on one archetype and another thing on the
 * next — the defect `StateSlot`'s own doc comment records. Only the region
 * headings and the stamp label are new, and they live in `hydroma.chrome`.
 */
export async function hydromaLabels(): Promise<TemplateLabels> {
  const [chrome, common, status, market, offline] = await Promise.all([
    getTranslations('hydroma.chrome'),
    getTranslations('common'),
    getTranslations('statusLine'),
    getTranslations('market.template'),
    getTranslations('offline'),
  ]);

  return {
    loading: status('noData'),
    empty: market('unavailableDescription'),
    error: common('error'),
    offline: offline('description'),
    partial: market('unavailableDescription'),
    action: common('retry'),
    provenance: chrome('provenance'),
    live: chrome('live'),
    unavailable: chrome('unavailable'),
    footer: chrome('footer'),
    regions: {
      title: chrome('regions.title'),
      status: chrome('regions.status'),
      provenance: chrome('regions.provenance'),
      filters: chrome('regions.filters'),
      state: chrome('regions.state'),
      data: chrome('regions.data'),
      navigation: chrome('regions.navigation'),
      actions: chrome('regions.actions'),
      summary: chrome('regions.summary'),
      detail: chrome('regions.detail'),
      notes: chrome('regions.notes'),
      print: chrome('regions.print'),
      footer: chrome('regions.footer'),
    },
  };
}

/** A JSON value rendered as text, without lying about its type. */
export function scalar(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.map((item) => scalar(item)).join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/** `"1,204.5"` — the grouped form a table cell reads as one number. */
export function number(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return scalar(value);
  return value.toLocaleString('en-US', { maximumFractionDigits: 6 });
}
