import { useCallback, useEffect, useState } from 'react';
import Seo from '../../../components/ui/Seo';
import { modelsApi } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import { KeyValues, SectionCard, StateBanner, useLiveState } from '../../../components/dashboard/LivePanel';

interface RegistryParam {
  name: string;
  label: string;
  unit?: string;
  default?: number | string | null;
  kind?: string; // float | int | str | select
}

interface RegistryModel {
  slug: string;
  name_fa?: string;
  name_en?: string;
  domain?: string;
  fidelity?: string;
  reference?: string;
  description?: string;
  params?: RegistryParam[];
  [key: string]: unknown;
}

function defaultValue(param: RegistryParam): string {
  if (param.default === null || param.default === undefined) return '';
  return String(param.default);
}

function parseValue(kind: string | undefined, raw: string): unknown {
  const trimmed = raw.trim();
  if (trimmed === '') return undefined;
  if (kind === 'int') return Math.trunc(Number(trimmed));
  if (kind === 'float') return Number(trimmed);
  return trimmed; // str / select
}

/** A5 — live scientific model registry (22 models via /api/v1/models). */
export default function LiveIndicesPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const list = useLiveState();
  const run = useLiveState();
  const [models, setModels] = useState<RegistryModel[]>([]);
  const [selected, setSelected] = useState<RegistryModel | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [runResult, setRunResult] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(async () => {
    const res = await list.run(() => modelsApi.list());
    if (res) {
      const body = res as Record<string, unknown>;
      const arr = Array.isArray(body.models) ? (body.models as RegistryModel[]) : [];
      setModels(arr);
    }
  }, [list]);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectModel = (model: RegistryModel) => {
    setSelected(model);
    setRunResult(null);
    const initial: Record<string, string> = {};
    for (const param of model.params ?? []) initial[param.name] = defaultValue(param);
    setValues(initial);
  };

  const runModel = async () => {
    if (!selected) return;
    setRunResult(null);
    const params: Record<string, unknown> = {};
    for (const param of selected.params ?? []) {
      const value = parseValue(param.kind, values[param.name] ?? '');
      if (value !== undefined) params[param.name] = value;
    }
    const res = await run.run(() => modelsApi.run(selected.slug, params));
    if (res) setRunResult(res as Record<string, unknown>);
  };

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  return (
    <div className="flex flex-col gap-5">
      <Seo
        title={`${isFa ? 'مدل‌های علمی هیدروما (زنده)' : 'Live HyDroMa models'} | ${t.brand.name}`}
        path="/dashboard/live/indices"
      />
      <h1 className="text-2xl font-extrabold text-ink-1">
        {isFa ? 'مدل‌های علمی هیدروما (اجرای زنده)' : 'Live HyDroMa scientific models'}
      </h1>

      <SectionCard title={isFa ? 'مدل‌های موجود' : 'Available models'}>
        <StateBanner state={list.state} error={list.error} retry={load} />
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {models.map((model) => {
            const slug = String(model.slug);
            const name = isFa ? (model.name_fa ?? slug) : (model.name_en ?? slug);
            return (
              <button
                key={slug}
                type="button"
                onClick={() => selectModel(model)}
                className={`glass glass-hover rounded-2xl p-4 text-start ${selected?.slug === slug ? 'ring-glow' : ''}`}
              >
                <p className="text-xs font-extrabold text-ink-1" dir="ltr">{slug}</p>
                <p className="mt-1 text-[11px] leading-5 text-ink-3">{name}</p>
                <p className="mt-1 text-[10px] font-bold text-aqua-300" dir="ltr">{model.fidelity ?? ''}</p>
              </button>
            );
          })}
        </div>
        {models.length === 0 && list.state === 'done' ? (
          <p className="mt-3 text-xs text-ink-3">
            {isFa ? 'مدلی از سرور دریافت نشد — سرویس بک‌اند را بررسی کنید.' : 'No model list received from the gateway.'}
          </p>
        ) : null}
      </SectionCard>

      {selected ? (
        <SectionCard title={`${isFa ? 'اجرای مدل' : 'Run model'} — ${selected.slug}`}>
          <div className="grid gap-3 sm:grid-cols-2">
            {(selected.params ?? []).map((param) => (
              <label key={param.name} className="flex flex-col gap-1">
                <span className="text-[11px] font-bold text-ink-3">
                  {param.label}
                  {param.unit ? <span className="text-ink-4"> ({param.unit})</span> : null}
                </span>
                <input
                  type={param.kind === 'int' || param.kind === 'float' ? 'number' : 'text'}
                  step="any"
                  dir="ltr"
                  value={values[param.name] ?? ''}
                  onChange={(event) => setValues((prev) => ({ ...prev, [param.name]: event.target.value }))}
                  className={inputCls}
                />
              </label>
            ))}
          </div>
          <button
            type="button"
            onClick={runModel}
            disabled={run.state === 'loading'}
            className="mt-4 rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {run.state === 'loading' ? (isFa ? 'در حال اجرا…' : 'Running…') : isFa ? 'اجرای مدل' : 'Run model'}
          </button>
          <div className="mt-3">
            <StateBanner state={run.state} error={run.error} retry={runModel} />
          </div>
        </SectionCard>
      ) : null}

      {runResult ? (
        <SectionCard title={isFa ? 'خروجی مدل' : 'Run result'}>
          <KeyValues data={runResult} />
        </SectionCard>
      ) : null}
    </div>
  );
}
