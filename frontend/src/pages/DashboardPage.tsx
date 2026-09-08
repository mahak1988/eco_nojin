/** HyDroMa science dashboard — 12-package portfolio + live model calculators
 * + model registry (zero-orphan) + central data hub (per-user aggregation). */

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCcw, Share2, ShieldCheck, User, Settings } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { dashboard } from '../content/pages/dashboard';
import { categories as registryCategories, registry, registryStats } from '../lib/hydromaregistry';
import { fetchHubRuns, setHubRunShared, type HubRun } from '../lib/hub';
import { buildCalculatorLabels } from '../components/dashboard/calculators';
import {
  HortonCalculator,
  HydraulicsCalculator,
  RingCalculator,
  ScsCalculator,
  VgCalculator,
} from '../components/dashboard/calculators';

type HubState = 'loading' | 'ready' | 'error';

function implChip(impl: string): { className: string; label: string } {
  const isCalc = impl === 'calculator' || impl === 'engine+calculator';
  return {
    className: isCalc ? 'bg-aqua-500/12 text-aqua-300' : 'bg-white/8 text-emerald-100/55',
    label:
      impl === 'calculator'
        ? 'محاسبه‌گر داشبورد'
        : impl === 'engine+calculator'
          ? 'موتور + محاسبه‌گر'
          : impl === 'engine+api'
            ? 'موتور + API'
            : 'موتور بک‌اند',
  };
}

function implChipEn(impl: string): { className: string; label: string } {
  const isCalc = impl === 'calculator' || impl === 'engine+calculator';
  return {
    className: isCalc ? 'bg-aqua-500/12 text-aqua-300' : 'bg-white/8 text-emerald-100/55',
    label:
      impl === 'calculator'
        ? 'dashboard calculator'
        : impl === 'engine+calculator'
          ? 'engine + calculator'
          : impl === 'engine+api'
            ? 'engine + API'
            : 'backend engine',
  };
}

/** HyDroMa dashboard — prepared per the engineering booklets HP-01..HP-12. */
export default function DashboardPage() {
  const { lang, t } = useLang();
  const c = dashboard[lang as 'fa' | 'en'];

  const [runs, setRuns] = useState<HubRun[]>([]);
  const [hubState, setHubState] = useState<HubState>('loading');

  const loadRuns = useCallback(async () => {
    setHubState('loading');
    try {
      setRuns(await fetchHubRuns());
      setHubState('ready');
    } catch (error) {
      console.error('hub listing failed', error);
      setHubState('error');
    }
  }, []);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  const toggleShare = async (run: HubRun) => {
    try {
      await setHubRunShared(run.id, !run.shared);
      await loadRuns();
    } catch (error) {
      console.error('share toggle failed', error);
    }
  };

  const calcLabels = buildCalculatorLabels(lang);

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/dashboard" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      {/* calculators */}
      <section className="px-4 py-10 sm:px-6" id="calculators">
        <div className="mx-auto flex max-w-4xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.calcTitle} lead={c.calcLead} />
          <div className="flex flex-col gap-4">
            <HortonCalculator labels={calcLabels.horton} />
            <ScsCalculator labels={calcLabels.scs} />
            <VgCalculator labels={calcLabels.vg} />
            <HydraulicsCalculator labels={calcLabels.hydraulics} />
            <RingCalculator labels={calcLabels.ring} />
          </div>
          <p className="text-center text-[11px] text-emerald-100/35">{c.calcNote}</p>
        </div>
      </section>

      {/* central data hub */}
      <section className="px-4 py-10 sm:px-6" id="hub">
        <div className="mx-auto flex max-w-4xl flex-col gap-6">
          <SectionHeading
            kicker={lang === 'fa' ? 'مرکز تجمیع داده' : 'Data hub'}
            title={lang === 'fa' ? 'مرکز تجمیع اجراهای من' : 'My aggregated runs'}
            lead={
              lang === 'fa'
                ? 'هر محاسبه‌گر می‌تواند نتیجه را در مرکز تجمیع ثبت کند؛ اجراهای شما اینجا جمع می‌شوند و می‌توانید خروجی‌ها را برای سایرین به اشتراک بگذارید. کلید کاربر ناشناس است و هیچ IP/اطلاعات شخصی ذخیره نمی‌شود.'
                : 'Every calculator can register its result in the central hub; your runs are aggregated here and outputs can be shared publicly. The user key is anonymous — no IP or personal data is stored.'
            }
          />
          <div className="flex flex-wrap items-center gap-2">
            <Link to="/dashboard/profile" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold text-emerald-100/70">
              <User className="h-3.5 w-3.5" aria-hidden />
              {lang === 'fa' ? 'پروفایل' : 'Profile'}
            </Link>
            <Link to="/dashboard/settings" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold text-emerald-100/70">
              <Settings className="h-3.5 w-3.5" aria-hidden />
              {lang === 'fa' ? 'تنظیمات' : 'Settings'}
            </Link>
          </div>
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={loadRuns}
              className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-extrabold text-emerald-50"
            >
              <RefreshCcw className="h-3.5 w-3.5" aria-hidden />
              {lang === 'fa' ? 'به‌روزرسانی' : 'Refresh'}
            </button>
            <span className="text-[11px] text-emerald-100/35">
              {lang === 'fa' ? `${runs.length} اجرا` : `${runs.length} runs`}
            </span>
          </div>

          {hubState === 'loading' ? (
            <p className="glass rounded-2xl p-5 text-center text-sm text-emerald-100/55">
              {lang === 'fa' ? 'در حال دریافت از مرکز تجمیع…' : 'Loading from the hub…'}
            </p>
          ) : null}
          {hubState === 'error' ? (
            <p role="alert" className="rounded-2xl border border-red-400/30 bg-red-400/10 p-5 text-center text-sm font-bold text-red-300">
              {lang === 'fa'
                ? 'درگاه در دسترس نیست — سرویس بک‌اند را روی پورت ۸۰۰۰ اجرا کنید.'
                : 'Gateway unreachable — start the backend service on port 8000.'}
            </p>
          ) : null}
          {hubState === 'ready' && runs.length === 0 ? (
            <p className="glass rounded-2xl p-5 text-center text-sm text-emerald-100/55">
              {lang === 'fa'
                ? 'هنوز اجرایی ثبت نشده — از محاسبه‌گرهای بالا «ثبت در مرکز تجمیع» را بزنید.'
                : 'No runs yet — use “Register in hub” on the calculators above.'}
            </p>
          ) : null}

          {hubState === 'ready' && runs.length > 0 ? (
            <div className="flex flex-col gap-3">
              {runs.map((run) => (
                <div key={run.id} className="glass flex flex-col gap-2 rounded-2xl p-4 sm:flex-row sm:items-center">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-extrabold text-emerald-50" dir="ltr">
                      {run.title ?? run.model_id}
                    </p>
                    <p className="text-[11px] text-emerald-100/45" dir="ltr">
                      {run.model_id} · {run.created_at?.slice(0, 16).replace('T', ' ')}
                    </p>
                  </div>
                  {run.shared ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-leaf-500/15 px-3 py-1 text-[10px] font-bold text-leaf-300">
                      <Share2 className="h-3 w-3" aria-hidden />
                      {lang === 'fa' ? 'اشتراک عمومی' : 'Shared'}
                    </span>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => toggleShare(run)}
                    className="glass glass-hover rounded-full px-3.5 py-1.5 text-[11px] font-bold text-emerald-100/70"
                  >
                    {run.shared
                      ? lang === 'fa'
                        ? 'لغو اشتراک'
                        : 'Unshare'
                      : lang === 'fa'
                        ? 'به اشتراک بگذار'
                        : 'Share'}
                  </button>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      {/* model registry */}
      <section className="px-4 py-10 sm:px-6" id="registry">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading
            kicker={lang === 'fa' ? 'رجیستری مدل‌ها' : 'Model registry'}
            title={lang === 'fa' ? 'رجیستری کامل مدل‌های علمی' : 'Complete scientific model registry'}
            lead={
              lang === 'fa'
                ? `همهٔ ${registryStats.total} مدل موتور هیدروما اینجا ثبت شده‌اند — ${registryStats.calculators} محاسبه‌گر زندهٔ داشبورد + ${registryStats.engine} موتور بک‌اند. سیاست «صفر مدل یتیم»: هر مدل یا محاسبه‌گر دارد یا به صفحهٔ مرتبط لینک است.`
                : `All ${registryStats.total} HyDroMa engine models are registered here — ${registryStats.calculators} live dashboard calculators + ${registryStats.engine} backend engines. Zero-orphan policy: every model has a calculator or a linked page.`
            }
          />
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="glass rounded-2xl p-4 text-center">
              <p className="text-2xl font-extrabold text-gradient-leaf">{registryStats.total}</p>
              <p className="text-[11px] text-emerald-100/55">{lang === 'fa' ? 'مدل ثبت‌شده' : 'registered models'}</p>
            </div>
            <div className="glass rounded-2xl p-4 text-center">
              <p className="text-2xl font-extrabold text-gradient-leaf">{registryStats.calculators}</p>
              <p className="text-[11px] text-emerald-100/55">{lang === 'fa' ? 'محاسبه‌گر داشبورد' : 'dashboard calculators'}</p>
            </div>
            <div className="glass rounded-2xl p-4 text-center">
              <p className="text-2xl font-extrabold text-gradient-leaf">{registryStats.engine}</p>
              <p className="text-[11px] text-emerald-100/55">{lang === 'fa' ? 'موتور بک‌اند' : 'backend engines'}</p>
            </div>
          </div>

          {registryCategories.map((category) => {
            const entries = registry.filter((entry) => entry.category === category.key);
            if (entries.length === 0) return null;
            return (
              <Reveal key={category.key}>
                <div className="glass rounded-3xl p-6">
                  <h3 className="mb-4 flex items-center gap-2 text-sm font-extrabold text-emerald-50">
                    <ShieldCheck className="h-4 w-4 text-leaf-400" aria-hidden />
                    {lang === 'fa' ? category.nameFa : category.nameEn}
                    <span className="text-[11px] font-bold text-emerald-100/35">
                      ({entries.length})
                    </span>
                  </h3>
                  <div className="grid gap-2.5">
                    {entries.map((entry) => {
                      const chip = lang === 'fa' ? implChip(entry.impl) : implChipEn(entry.impl);
                      return (
                      <div key={entry.id} className="rounded-2xl bg-white/4 p-3.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-leaf-500/12 px-2.5 py-0.5 text-[10px] font-extrabold text-leaf-300" dir="ltr">
                            {entry.id}
                          </span>
                          <span className="text-xs font-extrabold text-emerald-50" dir="ltr">
                            {lang === 'fa' ? entry.nameFa : entry.nameEn}
                          </span>
                          <span
                            className={`ms-auto rounded-full px-2.5 py-0.5 text-[10px] font-bold ${chip.className}`}
                          >
                            {chip.label}
                          </span>
                        </div>
                        <p className="mt-1.5 text-xs leading-6 text-emerald-100/55">
                          {lang === 'fa' ? entry.descFa : entry.descEn}
                        </p>
                        <p className="mt-1 text-[10px] text-emerald-100/30" dir="ltr">
                          {entry.enginePath} · {entry.ref}
                        </p>
                      </div>
                      );
                    })}
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* portfolio */}
      <section className="px-4 py-10 sm:px-6" id="portfolio">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.portfolioTitle} lead={c.portfolioNote} />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {c.packages.map((pkg, index) => (
              <Reveal key={pkg.code} delay={(index % 3) * 0.06}>
                <article className="glass glass-hover flex h-full flex-col gap-2.5 rounded-3xl p-6">
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-full bg-leaf-500/12 px-3 py-1 text-[11px] font-extrabold text-leaf-300" dir="ltr">
                      {pkg.code}
                    </span>
                    <span className="text-[11px] font-bold text-aqua-300">{pkg.priority}</span>
                  </div>
                  <h3 className="text-base font-extrabold text-emerald-50">{pkg.title}</h3>
                  <p className="text-xs leading-6 text-emerald-100/60">{pkg.desc}</p>
                  <div className="mt-auto grid grid-cols-2 gap-2 pt-2">
                    <div className="rounded-xl bg-white/5 px-3 py-2">
                      <p className="text-[10px] text-emerald-100/40">CAPEX</p>
                      <p className="text-[11px] font-bold text-emerald-50">{pkg.capex}</p>
                    </div>
                    <div className="rounded-xl bg-white/5 px-3 py-2">
                      <p className="text-[10px] text-emerald-100/40">{lang === 'fa' ? 'بازگشت' : 'Payback'}</p>
                      <p className="text-[11px] font-bold text-emerald-50">{pkg.payback}</p>
                    </div>
                  </div>
                  <p className="pt-1 text-[10px] leading-5 text-aqua-300/70">{pkg.keyModels}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
