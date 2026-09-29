import { getTranslations } from 'next-intl/server';

import { SiteNav } from '@/components/SiteNav';
import { InstrumentPage } from '@/components/templates/InstrumentPage';
import { Badge } from '@/components/ui/Badge';
import { apiGet } from '@/lib/api/client';
import { verificationOf } from '@/lib/api/surfaces';

import {
  type CheckResult,
  hydromaLabels,
  number,
  PREVIEW_LIMIT,
  readRows,
  resolveState,
  type SuiteReport,
  scalar,
  stateDetail,
} from './hydroma';
import { ProvenanceBar } from './ProvenanceBar';
import { RecordScene, ToleranceChart } from './Scenes';

/**
 * The formula-verification suite — the one contract in this subtree that publishes
 * a calibration and an uncertainty, and it publishes them per check.
 *
 *   services/validation/formula_checks.py:36-48   `CheckResult(id, label, kind,
 *                                                 source, expected, actual,
 *                                                 tolerance, unit, passed, note)`
 *   services/validation/formula_checks.py:62       `passed = |expected − actual| <= tolerance`
 *   services/validation/formula_checks.py:79-82    `run_all()` → `{total, passed,
 *                                                 failed, pass_rate, checks}`
 *
 * `source` is the cited publication a check is judged against — a rational-method
 * unit identity, a published constant, a cross-module consistency requirement — so
 * it *is* the calibration, and `tolerance` is the bound the engine has to land
 * inside. Neither is a confidence interval over a prediction, and the page does
 * not claim one: the bar's confidence slot carries the tolerance, named as a
 * tolerance.
 *
 * `run_all()` publishes no run identifier and no timestamp, so that slot says the
 * contract does not publish one rather than showing the server's clock.
 */
const SUITE_PATH = '/api/v1/hydroma/validation';

/** The suite's own verdict fields, in the order `run_all()` publishes them. */
function headline(report: SuiteReport | null): string {
  if (!report) return '';
  return [
    `${report.total ?? 0}`,
    `${report.passed ?? 0}`,
    `${report.failed ?? 0}`,
    report.pass_rate ?? '',
  ]
    .filter((part) => part !== '')
    .join(' · ');
}

function errorOf(result: { ok: boolean; data?: unknown; error?: string }): string | null {
  if (!result.ok) return result.error ?? null;
  const data = result.data as { error?: unknown } | undefined;
  return typeof data?.error === 'string' ? data.error : null;
}

/* -------------------------------------------------------------------------- */
/* The check table                                                            */
/* -------------------------------------------------------------------------- */

async function CheckTable({
  checks,
  base,
  caption,
  headers,
}: {
  checks: readonly CheckResult[];
  base: string;
  caption: string;
  headers: { source: string; expected: string; actual: string; tolerance: string; unit: string };
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
              {headers.source}
            </th>
            <th scope="col" className="py-2 pe-3 text-end text-xs font-semibold text-ink-soft">
              {headers.expected}
            </th>
            <th scope="col" className="py-2 pe-3 text-end text-xs font-semibold text-ink-soft">
              {headers.actual}
            </th>
            <th scope="col" className="py-2 pe-3 text-end text-xs font-semibold text-ink-soft">
              {headers.tolerance}
            </th>
            <th scope="col" className="py-2 pe-3 text-end text-xs font-semibold text-ink-soft">
              {headers.unit}
            </th>
            <th scope="col" className="py-2 text-end text-xs font-semibold text-ink-soft">
              kind
            </th>
          </tr>
        </thead>
        <tbody>
          {checks.map((check) => (
            <tr key={check.id} className="border-b border-line align-top">
              <th scope="row" className="num py-2 pe-3 text-start font-normal">
                <a
                  href={`${base}?check_id=${encodeURIComponent(check.id)}`}
                  className="text-action underline decoration-line-strong underline-offset-2"
                >
                  {check.id}
                </a>
              </th>
              <td className="py-2 pe-3 text-ink-soft">{scalar(check.source)}</td>
              <td className="num py-2 pe-3 text-end text-ink">{scalar(check.expected)}</td>
              <td className="num py-2 pe-3 text-end text-ink">{scalar(check.actual)}</td>
              <td className="num py-2 pe-3 text-end text-ink-faint">{scalar(check.tolerance)}</td>
              <td className="num py-2 pe-3 text-end text-ink-faint">{scalar(check.unit)}</td>
              <td className="py-2 text-end">
                <Badge tone={check.passed ? 'success' : 'bad'} density="dense">
                  {check.passed ? '✓' : '✕'}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* The suite report                                                           */
/* -------------------------------------------------------------------------- */

export async function SuitePage({ locale }: { locale: string }) {
  const [meta, table, chart, labels] = await Promise.all([
    getTranslations('hydroma.pages.suite'),
    getTranslations('hydroma.table'),
    getTranslations('hydroma.chart'),
    hydromaLabels(),
  ]);

  const result = await apiGet<SuiteReport>(SUITE_PATH);
  const report = result.ok ? result.data : null;
  const checks = readRows<CheckResult>(result.ok ? result.data : undefined, 'checks');
  const state = resolveState(result, checks.length);
  const failure = errorOf(result);
  const tolerances = checks
    .map((check) => check.tolerance)
    .filter((value): value is number => typeof value === 'number');
  const sources = [...new Set(checks.map((check) => scalar(check.source)).filter(Boolean))];

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={meta('title')}
      description={meta('description')}
      labels={labels}
      path={SUITE_PATH}
      state={state}
      total={checks.length}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={stateDetail(SUITE_PATH, checks.length)}
      input={<SuitePanel path={SUITE_PATH} count={checks.length} headline={headline(report)} />}
      output={
        <div className="flex flex-col gap-3">
          {failure ? <p className="text-sm text-clay">{failure}</p> : null}
          <ToleranceChart checks={checks} />
          <CheckTable
            checks={checks.slice(0, PREVIEW_LIMIT)}
            base={`/${locale}/hydroma/validation/run`}
            caption={meta('title')}
            headers={{
              source: table('source'),
              expected: table('expected'),
              actual: table('actual'),
              tolerance: table('tolerance'),
              unit: table('unit'),
            }}
          />
        </div>
      }
      summary={
        <ProvenanceBar
          modelVersion={null}
          calibration={sources.length > 0 ? sources.join(' · ') : null}
          confidence={
            tolerances.length > 0
              ? chart('toleranceRange', {
                  min: number(Math.min(...tolerances)),
                  max: number(Math.max(...tolerances)),
                })
              : null
          }
          run={null}
        />
      }
      notes={<p className="text-sm text-ink-soft">{chart('suiteNote')}</p>}
    />
  );
}

async function SuitePanel({
  path,
  count,
  headline: verdict,
}: {
  path: string;
  count: number;
  headline: string;
}) {
  const t = await getTranslations('hydroma.suite');
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-ink-soft">{t('panelNote')}</p>
      <p className="num text-sm text-ink">{verdict}</p>
      <p className="num text-xs text-ink-faint">{t('count', { count })}</p>
      <p className="num break-all text-xs text-ink-faint">{path}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* The check catalogue                                                        */
/* -------------------------------------------------------------------------- */

/** `services/validation/router.py:32-44` — `{"checks": [...], "total": n}`. */
export async function SuiteChecksPage({ locale }: { locale: string }) {
  const [meta, table, labels] = await Promise.all([
    getTranslations('hydroma.pages.suiteChecks'),
    getTranslations('hydroma.table'),
    hydromaLabels(),
  ]);

  const endpoint = `${SUITE_PATH}/checks`;
  const result = await apiGet<SuiteReport>(endpoint);
  const checks = readRows<CheckResult>(result.ok ? result.data : undefined, 'checks');
  const state = resolveState(result, checks.length);

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={meta('title')}
      description={meta('description')}
      labels={labels}
      path={endpoint}
      state={state}
      total={checks.length}
      ok={result.ok}
      verified={result.ok && verificationOf(result.data)}
      stateDetail={stateDetail(endpoint, checks.length)}
      input={<SuitePanel path={endpoint} count={checks.length} headline="" />}
      output={
        <CheckTable
          checks={checks.slice(0, PREVIEW_LIMIT)}
          base={`/${locale}/hydroma/validation/run`}
          caption={meta('title')}
          headers={{
            source: table('source'),
            expected: table('expected'),
            actual: table('actual'),
            tolerance: table('tolerance'),
            unit: table('unit'),
          }}
        />
      }
      summary={
        <ProvenanceBar modelVersion={null} calibration={null} confidence={null} run={null} />
      }
      notes={<p className="text-sm text-ink-soft">{meta('note')}</p>}
    />
  );
}

/* -------------------------------------------------------------------------- */
/* One check                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * The one instrument on this surface that has a real parameter.
 *
 * `services/validation/router.py:8-29` takes `?check_id=`. Absent, it returns the
 * whole suite; present and unknown, it returns `{"error": "Check '…' not found"}`
 * with HTTP **200** — a successful response carrying a failure, which is why the
 * page reads `error` out of the body and shows it rather than reporting the run as
 * clean.
 */
export async function RunCheckPage({ locale, checkId }: { locale: string; checkId: string }) {
  const [meta, table, labels] = await Promise.all([
    getTranslations('hydroma.pages.suiteRun'),
    getTranslations('hydroma.table'),
    hydromaLabels(),
  ]);

  const endpoint = checkId
    ? `${SUITE_PATH}/run?check_id=${encodeURIComponent(checkId)}`
    : `${SUITE_PATH}/run`;
  const result = await apiGet<SuiteReport>(endpoint);
  const checks = readRows<CheckResult>(result.ok ? result.data : undefined, 'checks');
  const failure = errorOf(result);
  const state = resolveState(result, failure ? 0 : checks.length);

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={meta('title')}
      description={meta('description')}
      labels={labels}
      path={endpoint}
      state={state}
      total={checks.length}
      ok={result.ok && !failure}
      verified={false}
      stateDetail={stateDetail(endpoint, checks.length)}
      input={<RunPanel checkId={checkId} path={endpoint} />}
      output={
        <div className="flex flex-col gap-3">
          {failure ? <p className="text-sm text-clay">{failure}</p> : null}
          {checks.length > 0 ? (
            <RecordScene
              caption={meta('title')}
              entries={[
                { label: 'id', value: scalar(checks[0]?.id) },
                { label: 'label', value: scalar(checks[0]?.label) },
                { label: 'kind', value: scalar(checks[0]?.kind) },
                { label: table('source'), value: scalar(checks[0]?.source) },
                { label: table('expected'), value: scalar(checks[0]?.expected) },
                { label: table('actual'), value: scalar(checks[0]?.actual) },
                { label: table('tolerance'), value: scalar(checks[0]?.tolerance) },
                { label: table('unit'), value: scalar(checks[0]?.unit) },
                { label: 'passed', value: String(checks[0]?.passed ?? false) },
                { label: 'note', value: scalar(checks[0]?.note) },
              ]}
            />
          ) : null}
        </div>
      }
      summary={
        <ProvenanceBar
          modelVersion={null}
          calibration={scalar(checks[0]?.source) || null}
          confidence={typeof checks[0]?.tolerance === 'number' ? number(checks[0].tolerance) : null}
          run={null}
        />
      }
      notes={<p className="text-sm text-ink-soft">{meta('note')}</p>}
    />
  );
}

async function RunPanel({ checkId, path }: { checkId: string; path: string }) {
  const t = await getTranslations('hydroma.suite');
  return (
    <form method="get" action="" className="flex flex-col gap-3">
      <label htmlFor="hydroma-check-id" className="text-xs font-medium text-ink">
        check_id
      </label>
      <input
        id="hydroma-check-id"
        type="text"
        name="check_id"
        defaultValue={checkId}
        className="min-h-11 min-w-0 rounded-[var(--radius-s)] border border-line bg-surface px-3 py-2 text-sm text-ink"
      />
      <button
        type="submit"
        className="min-h-11 rounded-[var(--radius-s)] bg-action px-4 py-2 text-sm text-on-action"
      >
        {t('run')}
      </button>
      <p className="text-xs text-ink-soft">{t('runNote')}</p>
      <p className="num break-all text-xs text-ink-faint">{path}</p>
    </form>
  );
}

/* -------------------------------------------------------------------------- */
/* The reference data document                                                */
/* -------------------------------------------------------------------------- */

/**
 * `services/validation/router.py:47-58` reads `docs/hydroma/scientific_reference_data.json`
 * and returns `{"error": "Reference data file not found"}` when it is absent.
 *
 * **It is absent.** The file does not exist in the repository, so this contract
 * cannot answer with reference values today. The page says that in the error state
 * and names the file, rather than substituting the `source` strings from
 * `formula_checks` and calling them reference data. It also means
 * `formula_checks._reference_data()` returns `{}` for every run — which is why the
 * suite's checks carry their expected values inline instead of loading them.
 */
export async function ReferenceDataPage({ locale }: { locale: string }) {
  const [meta, table, labels] = await Promise.all([
    getTranslations('hydroma.pages.suiteReference'),
    getTranslations('hydroma.table'),
    hydromaLabels(),
  ]);

  const endpoint = `${SUITE_PATH}/reference-data`;
  const result = await apiGet<Record<string, unknown>>(endpoint);
  const document_ = result.ok ? result.data : null;
  const failure = errorOf(result);
  const entries = document_
    ? Object.entries(document_).map(([key, value]) => ({ key, value }))
    : [];
  const state = resolveState(result, failure || entries.length === 0 ? 0 : 1);

  return (
    <InstrumentPage
      nav={<SiteNav locale={locale} />}
      title={meta('title')}
      description={meta('description')}
      labels={labels}
      path={endpoint}
      state={state}
      total={failure ? 0 : 1}
      ok={result.ok && !failure}
      verified={false}
      stateDetail={stateDetail(endpoint, failure ? 0 : 1)}
      input={<ReferencePanel path={endpoint} />}
      output={
        <div className="flex flex-col gap-3">
          {failure ? <p className="text-sm text-clay">{failure}</p> : null}
          {entries.length > 0 ? (
            <RecordScene
              caption={meta('title')}
              entries={entries.map((entry) => ({
                label: entry.key,
                value: scalar(entry.value).slice(0, 400),
              }))}
            />
          ) : null}
          <p className="text-xs text-ink-faint">{table('source')}</p>
        </div>
      }
      summary={
        <ProvenanceBar modelVersion={null} calibration={null} confidence={null} run={null} />
      }
      notes={<p className="text-sm text-ink-soft">{meta('note')}</p>}
    />
  );
}

async function ReferencePanel({ path }: { path: string }) {
  const t = await getTranslations('hydroma.suite');
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-ink-soft">{t('referenceNote')}</p>
      <p className="num break-all text-xs text-ink-faint">{path}</p>
      <p className="num break-all text-xs text-ink-faint">{t('referenceFile')}</p>
    </div>
  );
}
