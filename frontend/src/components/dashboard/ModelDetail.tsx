/** Model detail — shared renderer for every dashboard model page
 * (src/pages/dashboard/<category>/*.tsx). Embeds the live calculator for
 * formula models and related links for engine models. */

import { Link } from 'react-router-dom';
import { ArrowLeft, FileCode2, FlaskConical, ScrollText } from 'lucide-react';
import Seo from '../ui/Seo';
import Reveal from '../ui/Reveal';
import { categories as registryCategories, registry } from '../../lib/hydromaregistry';
import { useLang } from '../../i18n/LanguageContext';
import {
  buildCalculatorLabels,
  HortonCalculator,
  HydraulicsCalculator,
  RingCalculator,
  ScsCalculator,
  VgCalculator,
} from './calculators';
import IndexRunner from './IndexRunner';
import { engineClientFor } from '../../lib/hydromaTools';
import EtCalculatorRunner from './EtCalculatorRunner';
import MrvSatelliteRunner from './MrvSatelliteRunner';
import ChainRunner from './ChainRunner';
import MrvIotRunner from './MrvIotRunner';
import MrvCitizenRunner from './MrvCitizenRunner';
import MrvQaRunner from './MrvQaRunner';
import MrvMetricsRunner from './MrvMetricsRunner';

const CALC_MAP: Record<string, 'horton' | 'scs' | 'vg' | 'hydraulics' | 'ring'> = {
  'horton-infiltration': 'horton',
  'scs-cn-runoff': 'scs',
  'van-genuchten': 'vg',
  'manning-channel': 'hydraulics',
  'reynolds-number': 'hydraulics',
  'froude-number': 'hydraulics',
  'francis-weir': 'hydraulics',
  'darcy-law': 'ring',
  'ring-storage': 'ring',
  'effective-porosity': 'ring',
};

/** Renders a single registry model as a full dashboard page. */
export default function ModelDetail({ modelId }: { modelId: string }) {
  const { t, lang } = useLang();
  const isFa = lang === 'fa';
  const entry = registry.find((item) => item.id === modelId);

  if (!entry) {
    return (
      <div className="glass rounded-3xl p-8 text-center">
        <p className="text-sm text-[var(--color-night-200)]/60">
          {isFa ? 'مدل در رجیستری یافت نشد.' : 'Model not found in the registry.'}
        </p>
        <Link to="/dashboard" className="mt-3 inline-block text-xs font-bold text-[var(--color-leaf-300)] hover:underline">
          {isFa ? 'بازگشت به داشبورد هیدروما' : 'Back to HyDroMa dashboard'}
        </Link>
      </div>
    );
  }

  const category = registryCategories.find((item) => item.key === entry.category);
  const calcKey = CALC_MAP[entry.id];
  const toolApi = engineClientFor(entry.id);
  const labels = buildCalculatorLabels(lang);

  const implLabel = isFa
    ? entry.impl === 'calculator'
      ? 'محاسبه‌گر داشبورد'
      : entry.impl === 'engine+calculator'
        ? 'موتور + محاسبه‌گر'
        : entry.impl === 'engine+api'
          ? 'موتور + API'
          : 'موتور بک‌اند'
    : entry.impl === 'calculator'
      ? 'dashboard calculator'
      : entry.impl === 'engine+calculator'
        ? 'engine + calculator'
        : entry.impl === 'engine+api'
          ? 'engine + API'
          : 'backend engine';

  return (
    <div className="flex flex-col gap-6">
      <Seo
        title={`${isFa ? entry.nameFa : entry.nameEn} | ${t.brand.name}`}
        description={isFa ? entry.descFa : entry.descEn}
        path={`/dashboard/models/${entry.id}`}
      />

      <Reveal className="flex flex-col gap-3">
        <Link
          to="/dashboard"
          className="inline-flex w-fit items-center gap-2 text-xs font-bold text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)]"
        >
          <ArrowLeft className={`h-3.5 w-3.5 ${isFa ? '' : 'rotate-180'}`} aria-hidden />
          {isFa ? 'بازگشت به داشبورد هیدروما' : 'Back to HyDroMa dashboard'}
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-[var(--color-leaf-500)]/12 px-3 py-1 text-[11px] font-extrabold text-[var(--color-leaf-300)]" dir="ltr">
            {entry.id}
          </span>
          <span className="rounded-full bg-[var(--color-aqua-500)]/12 px-3 py-1 text-[11px] font-bold text-[var(--color-aqua-300)]">
            {isFa ? (category?.nameFa ?? entry.category) : (category?.nameEn ?? entry.category)}
          </span>
          <span
            className={`rounded-full px-3 py-1 text-[11px] font-bold ${
              entry.impl.includes('calculator') ? 'bg-violet-400/15 text-violet-300' : 'bg-white/8 text-[var(--color-night-200)]/55'
            }`}
          >
            {implLabel}
          </span>
        </div>
        <h1 className="text-2xl font-extrabold leading-snug text-[var(--color-night-100)] sm:text-3xl" dir="ltr">
          {isFa ? entry.nameFa : entry.nameEn}
        </h1>
        <p className="max-w-3xl text-sm leading-8 text-[var(--color-night-200)]/65">
          {isFa ? entry.descFa : entry.descEn}
        </p>
        <p className="text-xs text-[var(--color-night-200)]/40" dir="ltr">
          <FileCode2 className="me-1.5 inline h-3.5 w-3.5" aria-hidden />
          {entry.enginePath} · {entry.ref}
        </p>
      </Reveal>

      {calcKey ? (
        <Reveal className="flex flex-col gap-3">
          <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
            <FlaskConical className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />
            {isFa ? 'محاسبه‌گر زنده' : 'Live calculator'}
          </h2>
          {calcKey === 'horton' ? <HortonCalculator labels={labels.horton} /> : null}
          {calcKey === 'scs' ? <ScsCalculator labels={labels.scs} /> : null}
          {calcKey === 'vg' ? <VgCalculator labels={labels.vg} /> : null}
          {calcKey === 'hydraulics' ? <HydraulicsCalculator labels={labels.hydraulics} /> : null}
          {calcKey === 'ring' ? <RingCalculator labels={labels.ring} /> : null}
        </Reveal>
      ) : toolApi ? (
        <Reveal className="flex flex-col gap-3">
          <IndexRunner modelId={entry.id} api={toolApi} />
        </Reveal>
      ) : entry.id === 'et-calculator' ? (
        <Reveal className="flex flex-col gap-3">
          <EtCalculatorRunner />
        </Reveal>
      ) : entry.id === 'sim-orchestrator' ? (
        <Reveal className="flex flex-col gap-3">
          <ChainRunner />
        </Reveal>
      ) : entry.id === 'mrv-satellite' ? (
        <Reveal className="flex flex-col gap-3">
          <MrvSatelliteRunner />
        </Reveal>
      ) : entry.id === 'mrv-iot' ? (
        <Reveal className="flex flex-col gap-3">
          <MrvIotRunner />
        </Reveal>
      ) : entry.id === 'mrv-citizen' ? (
        <Reveal className="flex flex-col gap-3">
          <MrvCitizenRunner />
        </Reveal>
      ) : entry.id === 'mrv-qa' ? (
        <Reveal className="flex flex-col gap-3">
          <MrvQaRunner />
        </Reveal>
      ) : entry.id === 'mrv-metrics' ? (
        <Reveal className="flex flex-col gap-3">
          <MrvMetricsRunner />
        </Reveal>
      ) : (
        <Reveal>
          <div className="glass flex items-start gap-3 rounded-2xl p-5">
            <FlaskConical className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-aqua-300)]" aria-hidden />
            <p className="text-xs leading-6 text-[var(--color-night-200)]/60">
              {isFa
                ? 'این مدل روی هستهٔ علمی هیدروما (Python/C++) اجرا می‌شود و از طریق درگاه API پلتفرم قابل فراخوانی است.'
                : 'This model runs on the HyDroMa scientific core (Python/C++) and is callable through the platform API gateway.'}
            </p>
          </div>
        </Reveal>
      )}

      <Reveal>
        <div className="glass flex flex-wrap items-center gap-2 rounded-2xl p-4 text-xs">
          <ScrollText className="h-4 w-4 text-[var(--color-leaf-400)]/80" aria-hidden />
          <span className="font-bold text-[var(--color-night-200)]/60">{isFa ? 'پیوندهای مرتبط:' : 'Related:'}</span>
          <Link to="/transparency" className="rounded-full bg-white/5 px-3 py-1 font-bold text-[var(--color-night-200)]/70 hover:text-[var(--color-leaf-300)]">
            {t.footer.quickLinks.transparency}
          </Link>
          <Link to="/terms" className="rounded-full bg-white/5 px-3 py-1 font-bold text-[var(--color-night-200)]/70 hover:text-[var(--color-leaf-300)]">
            {t.footer.legalLinks.terms}
          </Link>
          <Link to="/eco-coin" className="rounded-full bg-white/5 px-3 py-1 font-bold text-[var(--color-night-200)]/70 hover:text-[var(--color-leaf-300)]">
            Eco Coin
          </Link>
        </div>
      </Reveal>
    </div>
  );
}
