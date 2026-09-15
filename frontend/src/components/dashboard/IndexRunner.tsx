/** Live runner for the HyDroMa engine tool APIs (indices, soil, water,
 * climate, carbon, economics, simulation). Fetches parameter metadata from
 * the gateway, renders an input form, executes server-side, and presents
 * results with a chart, provenance and hub registration. Pure computation
 * -> no auth required. */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Check, Copy, Database, FlaskConical, Loader2, Play, RotateCcw } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import type { EngineApiClient, EngineModelMeta, EngineParamSpec } from '../../lib/hydromaEngine';
import { submitHubRun } from '../../lib/hub';
import { getApiBase } from '../../lib/api';

type Phase = 'loading' | 'ready' | 'error';

function formatScalar(value: unknown): string {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return String(value);
    return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(4)));
  }
  if (typeof value === 'string') return value;
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (value === null || value === undefined) return '—';
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    if (value.length > 12) return `[${value.slice(0, 12).map(formatScalar).join(', ')}, …] (${value.length})`;
    return `[${value.map(formatScalar).join(', ')}]`;
  }
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/** Flattens a nested result object into [label, value] pairs for the table. */
function flattenResult(value: unknown, prefix = ''): Array<[string, string]> {
  const out: Array<[string, string]> = [];
  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      const label = prefix ? `${prefix}.${key}` : key;
      if (child !== null && typeof child === 'object' && !Array.isArray(child)) {
        out.push(...flattenResult(child, label));
      } else {
        out.push([label, formatScalar(child)]);
      }
    }
  } else {
    out.push([prefix || 'result', formatScalar(value)]);
  }
  return out;
}

interface Series {
  x: number[];
  y: number[];
  xLabel: string;
  yLabel: string;
}

/** Finds a plottable series: a curve of {x,y}-ish objects, or a number array. */
function extractSeries(result: Record<string, unknown>): Series | null {
  const numericKeys = (obj: Record<string, unknown>): string[] =>
    Object.entries(obj)
      .filter(([, v]) => typeof v === 'number' && Number.isFinite(v))
      .map(([k]) => k);

  const curve = result.curve;
  if (Array.isArray(curve) && curve.length >= 3 && typeof curve[0] === 'object' && curve[0] !== null) {
    const keys = numericKeys(curve[0] as Record<string, unknown>);
    if (keys.length >= 2) {
      const [xKey, yKey] = keys;
      const xs: number[] = [];
      const ys: number[] = [];
      for (const row of curve as Record<string, unknown>[]) {
        const x = row[xKey];
        const y = row[yKey];
        if (typeof x === 'number' && typeof y === 'number') {
          xs.push(x);
          ys.push(y);
        }
      }
      if (xs.length >= 3) return { x: xs, y: ys, xLabel: xKey, yLabel: yKey };
    }
  }

  for (const [key, value] of Object.entries(result)) {
    if (Array.isArray(value) && value.length >= 3 && value.every((v) => typeof v === 'number')) {
      return {
        x: value.map((_, i) => i + 1),
        y: value as number[],
        xLabel: 'index',
        yLabel: key,
      };
    }
  }
  return null;
}

function SeriesChart({ series }: { series: Series }) {
  const { x, y } = series;
  const reduceMotion = useReducedMotion();
  const w = 480;
  const h = 180;
  const pad = 28;
  const xmin = Math.min(...x);
  const xmax = Math.max(...x);
  const ymin = Math.min(...y);
  const ymax = Math.max(...y);
  const sx = (v: number) => pad + ((v - xmin) / (xmax - xmin || 1)) * (w - pad * 2);
  const sy = (v: number) => h - pad - ((v - ymin) / (ymax - ymin || 1)) * (h - pad * 2);
  const points = x.map((v, i) => `${sx(v).toFixed(1)},${sy(y[i]).toFixed(1)}`).join(' ');

  return (
    <figure className="glass rounded-2xl p-4">
      <figcaption className="mb-2 flex items-center justify-between text-[11px] font-bold text-[var(--color-night-200)]/55">
        <span dir="ltr">{series.yLabel}</span>
        <span dir="ltr">{series.xLabel}</span>
      </figcaption>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" role="img" aria-label="result chart">
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="rgba(134,226,172,0.25)" strokeWidth="1" />
        <line x1={pad} y1={pad} x2={pad} y2={h - pad} stroke="rgba(134,226,172,0.25)" strokeWidth="1" />
        <motion.polyline
          points={points}
          fill="none"
          stroke="#5fd49a"
          strokeWidth="2"
          strokeLinejoin="round"
          initial={reduceMotion ? false : { pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.8, ease: 'easeInOut' }}
        />
        <motion.g initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.4, duration: 0.6 }}>
          {x.map((v, i) => (
            <circle key={i} cx={sx(v)} cy={sy(y[i])} r="2.5" fill="#8fd8e6" />
          ))}
        </motion.g>
        <text x={pad} y={12} fill="rgba(233,246,240,0.5)" fontSize="9" textAnchor="start">
          {ymax.toPrecision(4)}
        </text>
        <text x={pad} y={h - pad + 12} fill="rgba(233,246,240,0.5)" fontSize="9" textAnchor="start">
          {xmin.toPrecision(4)}
        </text>
        <text x={w - pad} y={h - pad + 12} fill="rgba(233,246,240,0.5)" fontSize="9" textAnchor="end">
          {xmax.toPrecision(4)}
        </text>
      </svg>
    </figure>
  );
}

function defaultValueToString(param: EngineParamSpec): string {
  const value = param.default;
  if (value === undefined || value === null) return '';
  if (Array.isArray(value)) return value.join(', ');
  return String(value);
}

function stringToValue(kind: EngineParamSpec['kind'], raw: string): unknown {
  const trimmed = raw.trim();
  if (kind === 'float') return trimmed === '' ? undefined : Number(trimmed);
  if (kind === 'int') return trimmed === '' ? undefined : Math.trunc(Number(trimmed));
  if (kind === 'select' || kind === 'str') return trimmed;
  if (kind === 'list_float') {
    const parts = trimmed.split(/[,;]/).map((p) => p.trim()).filter((p) => p !== '');
    if (parts.length === 0) return undefined;
    return parts.map((p) => Number(p));
  }
  if (kind === 'list_str') {
    const parts = trimmed.split(/[,;]/).map((p) => p.trim()).filter((p) => p !== '');
    if (parts.length === 0) return undefined;
    return parts;
  }
  return trimmed;
}

interface IndexRunnerProps {
  modelId: string;
  /** Engine API client; resolved from the tool mapping by the caller. */
  api: EngineApiClient;
}

export default function IndexRunner({ modelId, api }: IndexRunnerProps) {
  const { lang } = useLang();

  const isFa = lang === 'fa';

  const [meta, setMeta] = useState<EngineModelMeta | null>(null);
  const [phase, setPhase] = useState<Phase>('loading');
  const [loadError, setLoadError] = useState<string>('');
  const [values, setValues] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [rawResult, setRawResult] = useState<Record<string, unknown> | null>(null);
  const [sentParams, setSentParams] = useState<Record<string, unknown> | null>(null);
  const [runError, setRunError] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [hubState, setHubState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const load = useCallback(async () => {
    setPhase('loading');
    setLoadError('');
    try {
      const model = await api.detail(modelId);
      setMeta(model);
      const initial: Record<string, string> = {};
      for (const param of model.params) initial[param.name] = defaultValueToString(param);
      setValues(initial);
      setRawResult(null);
      setRunError('');
      setPhase('ready');
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : String(error));
      setPhase('error');
    }
  }, [api, modelId]);

  useEffect(() => {
    void load();
  }, [load]);

  const series = useMemo(() => (rawResult ? extractSeries(rawResult) : null), [rawResult]);
  const rows = useMemo(() => (rawResult ? flattenResult(rawResult) : null), [rawResult]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!meta) return;
    setRunning(true);
    setRunError('');
    setRawResult(null);
    setHubState('idle');
    const params: Record<string, unknown> = {};
    for (const param of meta.params) {
      const value = stringToValue(param.kind, values[param.name] ?? '');
      if (value !== undefined) params[param.name] = value;
    }
    try {
      const response = await api.run(modelId, params);
      setRawResult(response.result);
      setSentParams(params);
    } catch (error) {
      setRunError(error instanceof Error ? error.message : String(error));
    } finally {
      setRunning(false);
    }
  };

  const setParamValue = (name: string, raw: string) => {
    setValues((prev) => ({ ...prev, [name]: raw }));
  };

  const resetDefaults = () => {
    if (!meta) return;
    const initial: Record<string, string> = {};
    for (const param of meta.params) initial[param.name] = defaultValueToString(param);
    setValues(initial);
    setRawResult(null);
    setRunError('');
    setHubState('idle');
  };

  const copyJson = async () => {
    if (!rawResult) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(rawResult, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };

  const saveToHub = async () => {
    if (!rawResult) return;
    setHubState('saving');
    try {
      await submitHubRun({
        modelId,
        title: meta?.name_en ?? modelId,
        inputs: sentParams ?? {},
        outputs: rawResult,
      });
      setHubState('saved');
    } catch {
      setHubState('error');
    }
  };

  if (phase === 'loading') {
    return (
      <div className="glass flex items-center gap-3 rounded-2xl p-5 text-sm text-[var(--color-night-200)]/60">
        <Loader2 className="h-4 w-4 animate-spin text-[var(--color-leaf-300)]" aria-hidden />
        {isFa ? 'در حال بارگذاری پارامترهای مدل…' : 'Loading model parameters…'}
      </div>
    );
  }

  if (phase === 'error' || !meta) {
    return (
      <div className="rounded-2xl border border-red-400/30 bg-red-400/10 p-5 text-sm font-bold text-red-300" role="alert">
        {isFa ? 'اتصال به سرویس اجرا برقرار نشد.' : 'Runner unreachable.'}
        <p className="mt-1 break-all font-normal text-red-300/70" dir="ltr">{loadError}</p>
        <p className="mt-1 break-all font-normal text-red-300/70" dir="ltr">
          {isFa ? `آدرس پایه: ${getApiBase() || '(relative — پروکسی وایت یا هم-اصل)'}` : `Base URL: ${getApiBase() || '(relative — Vite proxy or same-origin)'}`}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="glass rounded-2xl p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h3 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
            <FlaskConical className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />
            {isFa ? 'اجرای زنده روی موتور علمی' : 'Live run on the scientific engine'}
          </h3>
          <button
            type="button"
            onClick={resetDefaults}
            className="inline-flex items-center gap-1.5 rounded-full bg-white/5 px-3 py-1 text-[11px] font-bold text-[var(--color-night-200)]/60 hover:text-[var(--color-leaf-300)]"
          >
            <RotateCcw className="h-3 w-3" aria-hidden />
            {isFa ? 'بازنشانی' : 'Defaults'}
          </button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {meta.params.map((param) => (
            <label key={param.name} className="flex flex-col gap-1.5">
              <span className="text-[11px] font-bold text-[var(--color-night-200)]/55" dir="ltr">
                {param.label}
                {param.unit ? <span className="text-[var(--color-night-200)]/35"> ({param.unit})</span> : null}
                {param.optional ? <span className="text-[var(--color-night-200)]/35"> · {isFa ? 'اختیاری' : 'optional'}</span> : null}
              </span>
              {param.kind === 'select' && param.options ? (
                <select
                  value={values[param.name] ?? ''}
                  onChange={(event) => setParamValue(param.name, event.target.value)}
                  className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
                >
                  {param.options.map((option) => (
                    <option key={option} value={option} className="bg-[#0b1526]">
                      {option}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={param.kind === 'float' || param.kind === 'int' ? 'number' : 'text'}
                  step={param.kind === 'float' || param.kind === 'int' ? 'any' : undefined}
                  dir="ltr"
                  value={values[param.name] ?? ''}
                  onChange={(event) => setParamValue(param.name, event.target.value)}
                  placeholder={param.kind === 'list_float' || param.kind === 'list_str' ? '1, 2, 3' : undefined}
                  className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 font-mono text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
                />
              )}
            </label>
          ))}
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={running}
            className="inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-5 py-2.5 text-sm font-extrabold text-white transition hover:bg-[var(--color-leaf-400)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Play className="h-4 w-4" aria-hidden />}
            {running ? (isFa ? 'در حال اجرا…' : 'Running…') : isFa ? 'اجرای مدل' : 'Run model'}
          </button>
          {rawResult ? (
            <>
              <button
                type="button"
                onClick={saveToHub}
                disabled={hubState === 'saving' || hubState === 'saved'}
                className="inline-flex items-center gap-1.5 rounded-full bg-white/5 px-4 py-2 text-[11px] font-bold text-[var(--color-night-200)]/70 transition hover:text-[var(--color-leaf-300)] disabled:opacity-60"
              >
                {hubState === 'saved' ? <Check className="h-3.5 w-3.5 text-[var(--color-leaf-300)]" aria-hidden /> : <Database className="h-3.5 w-3.5" aria-hidden />}
                {hubState === 'saved'
                  ? isFa ? 'ثبت شد' : 'Saved'
                  : hubState === 'saving'
                    ? isFa ? 'در حال ثبت…' : 'Saving…'
                    : isFa ? 'ثبت در مرکز داده' : 'Save to data hub'}
              </button>
              <button
                type="button"
                onClick={copyJson}
                className="inline-flex items-center gap-1.5 rounded-full bg-white/5 px-4 py-2 text-[11px] font-bold text-[var(--color-night-200)]/70 transition hover:text-[var(--color-leaf-300)]"
              >
                <Copy className="h-3.5 w-3.5" aria-hidden />
                {copied ? (isFa ? 'کپی شد' : 'Copied') : 'JSON'}
              </button>
            </>
          ) : null}
        </div>
        {hubState === 'error' ? (
          <p className="mt-2 text-[11px] font-bold text-sand-300">
            {isFa ? 'ثبت در مرکز داده ناموفق بود — اتصال سرویس را بررسی کنید.' : 'Hub registration failed — check the gateway connection.'}
          </p>
        ) : null}
      </form>

      {runError ? (
        <div className="rounded-2xl border border-red-400/30 bg-red-400/10 p-4 text-sm font-bold text-red-300" role="alert" dir="ltr">
          {runError}
        </div>
      ) : null}

      {rawResult ? (
        <>
          {series ? <SeriesChart series={series} /> : null}
          <div className="glass rounded-2xl p-5">
            <h3 className="mb-3 text-sm font-extrabold text-[var(--color-night-100)]">
              {isFa ? 'خروجی مدل' : 'Model output'}
            </h3>
            <dl className="divide-y divide-white/5">
              {(rows ?? []).map(([label, value]) => (
                <div key={label} className="flex flex-col gap-0.5 py-2 sm:flex-row sm:items-baseline sm:gap-4">
                  <dt className="shrink-0 font-mono text-[11px] font-bold text-[var(--color-leaf-300)] sm:w-52" dir="ltr">
                    {label}
                  </dt>
                  <dd className="break-words font-mono text-xs leading-6 text-[var(--color-night-100)]" dir="ltr">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="mt-3 border-t border-white/5 pt-3 text-[10px] leading-5 text-[var(--color-night-200)]/40" dir="ltr">
              {meta.reference}
            </p>
          </div>
        </>
      ) : null}
    </div>
  );
}
