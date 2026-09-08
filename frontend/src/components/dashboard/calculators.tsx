/** HyDroMa dashboard calculators — live implementations of the booklet
 * formulas (HP-01 F-01..F-06, HP-02 F-02..F-08, HP-03 F-01..F-09). */

import { useState, type ReactNode } from 'react';
import MiniChart from './MiniChart';
import { submitHubRun } from '../../lib/hub';
import { useLang } from '../../i18n/LanguageContext';
import {
  darcyFlow,
  effectivePorosity,
  francisWeirDischarge,
  froudeNumber,
  hortonCumulative,
  hortonRate,
  hydraulicRadius,
  manningDischarge,
  reynoldsNumber,
  ringStorageVolume,
  scsRetention,
  scsRunoff,
  vanGenuchtenTheta,
} from '../../lib/hydromamodels';

const inputCls =
  'w-full rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-emerald-50 focus:border-leaf-400/60 focus:outline-none';

function Field({
  label,
  value,
  onChange,
  step = 'any',
  min,
  suffix,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: string;
  min?: number;
  suffix?: string;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] font-bold text-emerald-100/60">
        {label} {suffix ? <span className="text-emerald-100/35">({suffix})</span> : null}
      </span>
      <input
        type="number"
        step={step}
        min={min}
        value={Number.isFinite(value) ? value : ''}
        onChange={(e) => onChange(Number(e.target.value))}
        className={inputCls}
      />
    </label>
  );
}

function Result({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="glass rounded-xl px-3 py-2">
      <p className="text-[10px] text-emerald-100/45">{label}</p>
      <p className="text-sm font-extrabold text-leaf-300" dir="ltr">
        {value} <span className="text-[10px] font-bold text-emerald-100/45">{unit}</span>
      </p>
    </div>
  );
}

function HubSubmitButton({
  modelId,
  title,
  payload,
}: {
  modelId: string;
  title: string;
  payload: { inputs: Record<string, unknown>; outputs: Record<string, unknown> };
}) {
  const { lang } = useLang();
  const [hubStatus, setHubStatus] = useState<'idle' | 'sending' | 'ok' | 'error'>('idle');
  const labels = {
    button: lang === 'fa' ? 'ثبت در مرکز تجمیع' : 'Register in hub',
    ok: lang === 'fa' ? 'در مرکز تجمیع ثبت شد ✓' : 'Registered in the hub ✓',
    error: lang === 'fa' ? 'ثبت ناموفق — درگاه در دسترس نیست.' : 'Registration failed — gateway unreachable.',
  };
  return (
    <div className="flex flex-col items-start gap-1.5">
      <button
        type="button"
        onClick={async () => {
          setHubStatus('sending');
          try {
            await submitHubRun({ modelId, title, inputs: payload.inputs, outputs: payload.outputs });
            setHubStatus('ok');
          } catch (submitError) {
            console.error('hub registration failed', submitError);
            setHubStatus('error');
          }
        }}
        disabled={hubStatus === 'sending'}
        className="rounded-full bg-aqua-500/15 px-4 py-1.5 text-[11px] font-extrabold text-aqua-300 transition-colors hover:bg-aqua-500/25 disabled:opacity-60"
      >
        {hubStatus === 'sending' ? '…' : labels.button}
      </button>
      {hubStatus === 'ok' ? <p className="text-[10px] font-bold text-leaf-300">{labels.ok}</p> : null}
      {hubStatus === 'error' ? (
        <p role="alert" className="text-[10px] font-bold text-red-300">
          {labels.error}
        </p>
      ) : null}
    </div>
  );
}

function CalcShell({
  title,
  formula,
  children,
}: {
  title: string;
  formula: string;
  children: ReactNode;
}) {
  return (
    <details className="glass group rounded-3xl open:border-leaf-500/30">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 p-5 text-sm font-extrabold text-emerald-50 marker:content-none [&::-webkit-details-marker]:hidden">
        {title}
        <span className="text-leaf-400 transition-transform group-open:rotate-45" aria-hidden>
          +
        </span>
      </summary>
      <div className="flex flex-col gap-4 border-t border-white/8 p-5">
        <p className="rounded-xl bg-black/30 px-4 py-2 text-center text-xs font-bold text-aqua-300" dir="ltr">
          {formula}
        </p>
        {children}
      </div>
    </details>
  );
}

/* ------------------------------------------------------------------ */
/* HP-01 F-01 — Horton infiltration                                    */
/* ------------------------------------------------------------------ */

export function HortonCalculator({ labels }: { labels: Record<string, string> }) {
  const [f0, setF0] = useState(130);
  const [fc, setFc] = useState(40);
  const [k, setK] = useState(0.5);
  const hours = [0, 1, 2, 3, 4, 5, 6];
  const rateSeries = hours.map((h) => ({ x: h, y: hortonRate(f0, fc, k, h) }));
  const cumSeries = hours.map((h) => ({ x: h, y: hortonCumulative(f0, fc, k, h) }));

  return (
    <CalcShell title={labels.title} formula="f(t) = fc + (f0 − fc)·e^(−k·t)   |   F(t) = fc·t + (f0−fc)/k·(1−e^(−k·t))">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Field label={labels.f0} value={f0} onChange={setF0} min={0} suffix="mm/h" />
        <Field label={labels.fc} value={fc} onChange={setFc} min={0} suffix="mm/h" />
        <Field label={labels.k} value={k} onChange={setK} min={0.01} step="0.05" suffix="1/h" />
        <Field label={labels.duration} value={6} onChange={() => {}} suffix="h" />
      </div>
      <MiniChart series={rateSeries} yLabel="f(t) mm/h" xLabel="t (h)" formatY={(v) => v.toFixed(0)} />
      <MiniChart series={cumSeries} yLabel="F(t) mm" xLabel="t (h)" formatY={(v) => v.toFixed(0)} />
      <div className="grid grid-cols-3 gap-2">
        <Result label={labels.f0} value={hortonRate(f0, fc, k, 0).toFixed(1)} unit="mm/h" />
        <Result label={labels.fc} value={hortonRate(f0, fc, k, 6).toFixed(1)} unit="mm/h" />
        <Result label={labels.cumulative6} value={hortonCumulative(f0, fc, k, 6).toFixed(0)} unit="mm" />
      </div>
      <HubSubmitButton
        modelId="horton-infiltration"
        title={labels.title}
        payload={{ inputs: { f0, fc, k }, outputs: { cum6: hortonCumulative(f0, fc, k, 6) } }}
      />
    </CalcShell>
  );
}

/* ------------------------------------------------------------------ */
/* HP-01/03 F-02/03 — SCS-CN runoff                                    */
/* ------------------------------------------------------------------ */

export function ScsCalculator({ labels }: { labels: Record<string, string> }) {
  const [cn, setCn] = useState(85);
  const rainfalls = [0, 10, 20, 30, 40, 50, 60, 80, 100];
  const series = rainfalls.map((p) => ({ x: p, y: scsRunoff(p, cn) }));
  const retention = scsRetention(cn);
  const q50 = scsRunoff(50, cn);

  return (
    <CalcShell title={labels.title} formula="S = 25400/CN − 254   |   Q = (P − 0.2S)² / (P + 0.8S)">
      <div className="grid grid-cols-2 gap-3">
        <Field label={labels.cn} value={cn} onChange={setCn} min={1} step="1" />
        <Result label={labels.retention} value={retention.toFixed(1)} unit="mm" />
      </div>
      <MiniChart series={series} yLabel="Q mm" xLabel="P mm" formatY={(v) => v.toFixed(0)} />
      <div className="grid grid-cols-2 gap-2">
        <Result label={labels.runoff50} value={q50.toFixed(1)} unit="mm" />
        <Result
          label={labels.hydroGoal}
          value={`${cn} → ${Math.max(30, Math.round(cn * 0.5))}`}
        />
      </div>
      <HubSubmitButton
        modelId="scs-cn-runoff"
        title={labels.title}
        payload={{ inputs: { cn }, outputs: { retention, q50 } }}
      />
    </CalcShell>
  );
}

/* ------------------------------------------------------------------ */
/* HP-01/06 F-04 — Van Genuchten retention curve                       */
/* ------------------------------------------------------------------ */

export function VgCalculator({ labels }: { labels: Record<string, string> }) {
  const [thetaR, setThetaR] = useState(0.05);
  const [thetaS, setThetaS] = useState(0.45);
  const [alpha, setAlpha] = useState(0.02);
  const [n, setN] = useState(1.5);
  const heads = [1, 3, 10, 30, 100, 300, 1000, 3300, 15000];
  const series = heads.map((h) => ({ x: h, y: vanGenuchtenTheta(h, thetaR, thetaS, alpha, n) }));
  const awc = vanGenuchtenTheta(330, thetaR, thetaS, alpha, n) - vanGenuchtenTheta(15000, thetaR, thetaS, alpha, n);

  return (
    <CalcShell title={labels.title} formula="θ(h) = θr + (θs − θr) / (1 + (α·h)^n)^m">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Field label={labels.thetaR} value={thetaR} onChange={setThetaR} step="0.01" />
        <Field label={labels.thetaS} value={thetaS} onChange={setThetaS} step="0.01" />
        <Field label={labels.alpha} value={alpha} onChange={setAlpha} step="0.005" suffix="1/cm" />
        <Field label={labels.n} value={n} onChange={setN} step="0.05" />
      </div>
      <MiniChart series={series} yLabel="θ cm³/cm³" xLabel="h (cm, log)" formatY={(v) => v.toFixed(2)} />
      <div className="grid grid-cols-2 gap-2">
        <Result label={labels.thetaSat} value={vanGenuchtenTheta(1, thetaR, thetaS, alpha, n).toFixed(3)} />
        <Result label={labels.awc} value={awc.toFixed(3)} unit="cm³/cm³" />
      </div>
      <HubSubmitButton
        modelId="van-genuchten"
        title={labels.title}
        payload={{ inputs: { thetaR, thetaS, alpha, n }, outputs: { awc } }}
      />
    </CalcShell>
  );
}

/* ------------------------------------------------------------------ */
/* HP-02 F-02..F-08 — channel hydraulics                               */
/* ------------------------------------------------------------------ */

export function HydraulicsCalculator({ labels }: { labels: Record<string, string> }) {
  const [n, setN] = useState(0.03);
  const [area, setArea] = useState(0.5);
  const [perimeter, setPerimeter] = useState(3.2);
  const [slope, setSlope] = useState(0.01);
  const [weirL, setWeirL] = useState(2);
  const [weirH, setWeirH] = useState(0.5);

  const radius = hydraulicRadius(area, perimeter);
  const q = manningDischarge(n, area, radius, slope);
  const velocity = area > 0 ? q / area : 0;
  const re = reynoldsNumber(velocity, radius * 2);
  const fr = froudeNumber(velocity, radius * 2);
  const weirQ = francisWeirDischarge(weirL, weirH);

  return (
    <CalcShell title={labels.title} formula="Q = (1/n)·A·R^⅔·S^½   |   Fr = v/√(g·D)   |   Q_weir = 1.84·L·H^1.5">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Field label={labels.manningN} value={n} onChange={setN} step="0.005" />
        <Field label={labels.area} value={area} onChange={setArea} step="0.05" suffix="m²" />
        <Field label={labels.perimeter} value={perimeter} onChange={setPerimeter} step="0.1" suffix="m" />
        <Field label={labels.slope} value={slope} onChange={setSlope} step="0.001" />
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Result label={labels.hydraulicR} value={radius.toFixed(3)} unit="m" />
        <Result label={labels.discharge} value={q.toFixed(3)} unit="m³/s" />
        <Result label={labels.reynolds} value={Math.round(re).toLocaleString('en-US')} />
        <Result label={labels.froude} value={fr.toFixed(3)} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field label={labels.weirL} value={weirL} onChange={setWeirL} step="0.1" suffix="m" />
        <Field label={labels.weirH} value={weirH} onChange={setWeirH} step="0.05" suffix="m" />
      </div>
      <Result label={labels.weirQ} value={weirQ.toFixed(3)} unit="m³/s" />
      <HubSubmitButton
        modelId="manning-channel"
        title={labels.title}
        payload={{
          inputs: { n, area, perimeter, slope, weirL, weirH },
          outputs: { q, reynolds: re, froude: fr, weirQ },
        }}
      />
    </CalcShell>
  );
}

/* ------------------------------------------------------------------ */
/* HP-03 F-01/02 — ring storage                                        */
/* ------------------------------------------------------------------ */

export function RingCalculator({ labels }: { labels: Record<string, string> }) {
  const [radius, setRadius] = useState(0.75);
  const [depth, setDepth] = useState(0.9);
  const layers = [
    { thickness: 0.15, porosity: 0.4 },
    { thickness: 0.45, porosity: 0.55 },
  ];
  const nEff = effectivePorosity(layers);
  const volume = ringStorageVolume(radius, depth, nEff);
  const darcy = darcyFlow(1e-5, 1, Math.PI * radius * radius);

  return (
    <CalcShell title={labels.title} formula="V = π·r²·h·n_eff   |   n_eff = Σ(hi·ni)/Σhi   |   q = K·i·A">
      <div className="grid grid-cols-2 gap-3">
        <Field label={labels.radius} value={radius} onChange={setRadius} step="0.05" suffix="m" />
        <Field label={labels.depth} value={depth} onChange={setDepth} step="0.05" suffix="m" />
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Result label={labels.nEff} value={nEff.toFixed(2)} />
        <Result label={labels.storage} value={(volume * 1000).toFixed(0)} unit="L" />
        <Result label={labels.darcy} value={(darcy * 3600 * 1000).toFixed(1)} unit="L/h" />
      </div>
      <HubSubmitButton
        modelId="ring-storage"
        title={labels.title}
        payload={{ inputs: { radius, depth }, outputs: { nEff, storageL: volume * 1000, darcyLh: darcy * 3600 * 1000 } }}
      />
    </CalcShell>
  );
}
