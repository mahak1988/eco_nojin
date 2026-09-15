/** HyDroMa science dashboard — 12-package portfolio + live model calculators
 * + model registry (zero-orphan) + central data hub (per-user aggregation). */

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCcw, Share2, User, Settings } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SpotlightCard from '../components/ui/SpotlightCard';
import SectionHeading from '../components/ui/SectionHeading';
import CategoryTree from '../components/dashboard/CategoryTree';
import EmptyBox from '../components/ui/EmptyBox';
import { useBilingual } from '../hooks/useBilingual';
import { useAuth } from '../context/AuthContext';
import { dashboard } from '../content/pages/dashboard';
import { registryStats } from '../lib/hydromaregistry';
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

/** HyDroMa dashboard — prepared per the engineering booklets HP-01..HP-12. */
export default function DashboardPage() {
  const { lang, t, fa } = useBilingual();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
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
            kicker={fa('مرکز تجمیع داده', 'Data hub')}
            title={fa('مرکز تجمیع اجراهای من', 'My aggregated runs')}
            lead={
              fa(
                'هر محاسبه‌گر می‌تواند نتیجه را در مرکز تجمیع ثبت کند؛ اجراهای شما اینجا جمع می‌شوند و می‌توانید خروجی‌ها را برای سایرین به اشتراک بگذارید. کلید کاربر ناشناس است و هیچ IP/اطلاعات شخصی ذخیره نمی‌شود.',
                'Every calculator can register its result in the central hub; your runs are aggregated here and outputs can be shared publicly. The user key is anonymous — no IP or personal data is stored.'
              )
            }
          />
          <div className="flex flex-wrap items-center gap-2">
            <Link to="/dashboard/profile" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold text-emerald-100/70">
              <User className="h-3.5 w-3.5" aria-hidden />
              {fa('پروفایل', 'Profile')}
            </Link>
            <Link to="/dashboard/settings" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold text-emerald-100/70">
              <Settings className="h-3.5 w-3.5" aria-hidden />
              {fa('تنظیمات', 'Settings')}
            </Link>
          </div>
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={loadRuns}
              className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-extrabold text-emerald-50"
            >
              <RefreshCcw className="h-3.5 w-3.5" aria-hidden />
              {fa('به‌روزرسانی', 'Refresh')}
            </button>
            <span className="text-[11px] text-emerald-100/35">
              {fa(`${runs.length} اجرا`, `${runs.length} runs`)}
            </span>
          </div>

          {hubState === 'loading' ? (
            <p className="glass rounded-2xl p-5 text-center text-sm text-emerald-100/55">
              {fa('در حال دریافت از مرکز تجمیع…', 'Loading from the hub…')}
            </p>
          ) : null}
          {hubState === 'error' ? (
            <p role="alert" className="rounded-2xl border border-red-400/30 bg-red-400/10 p-5 text-center text-sm font-bold text-red-300">
              {fa(
                'درگاه در دسترس نیست — سرویس بک‌اند را روی پورت ۸۰۰۰ اجرا کنید.',
                'Gateway unreachable — start the backend service on port 8000.'
              )}
            </p>
          ) : null}
          {hubState === 'ready' && runs.length === 0 ? (
            <EmptyBox
              icon="clipboard"
              title={fa('هنوز اجرایی ثبت نشده', 'No runs yet')}
              description={fa(
                'از محاسبه‌گرهای بالا «ثبت در مرکز تجمیع» را بزنید.',
                'Use "Register in hub" on the calculators above.'
              )}
              action={
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-5 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
                >
                  {fa('بازگشت به داشبورد', 'Back to dashboard')}
                </Link>
              }
            />
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
                      {fa('اشتراک عمومی', 'Shared')}
                    </span>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => toggleShare(run)}
                    className="glass glass-hover rounded-full px-3.5 py-1.5 text-[11px] font-bold text-emerald-100/70"
                  >
                    {run.shared
                      ? fa('لغو اشتراک', 'Unshare')
                      : fa('به اشتراک بگذار', 'Share')}
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
            kicker={fa('رجیستری مدل‌ها', 'Model registry')}
            title={fa('رجیستری کامل مدل‌های علمی', 'Complete scientific model registry')}
            lead={
              fa(
                `همهٔ ${registryStats.total} مدل موتور هیدروما اینجا ثبت شده‌اند — ${registryStats.calculators} محاسبه‌گر زندهٔ داشبورد + ${registryStats.engine} موتور بک‌اند. سیاست «صفر مدل یتیم»: هر مدل یا محاسبه‌گر دارد یا به صفحهٔ مرتبط لینک است.`,
                `All ${registryStats.total} HyDroMa engine models are registered here — ${registryStats.calculators} live dashboard calculators + ${registryStats.engine} backend engines. Zero-orphan policy: every model has a calculator or a linked page.`
              )
            }
          />
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="glass rounded-2xl p-4 text-center">
              <p className="text-2xl font-extrabold text-gradient-leaf">{registryStats.total}</p>
              <p className="text-[11px] text-emerald-100/55">{fa('مدل ثبت‌شده', 'registered models')}</p>
            </div>
            <div className="glass rounded-2xl p-4 text-center">
              <p className="text-2xl font-extrabold text-gradient-leaf">{registryStats.calculators}</p>
              <p className="text-[11px] text-emerald-100/55">{fa('محاسبه‌گر داشبورد', 'dashboard calculators')}</p>
            </div>
            <div className="glass rounded-2xl p-4 text-center">
              <p className="text-2xl font-extrabold text-gradient-leaf">{registryStats.engine}</p>
              <p className="text-[11px] text-emerald-100/55">{fa('موتور بک‌اند', 'backend engines')}</p>
            </div>
          </div>

          <CategoryTree />
        </div>
      </section>

      {/* live cards (Phase A/B) */}
      <section className="px-4 py-10 sm:px-6" id="live">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading
            kicker={fa('اتصال زنده', 'Live gateway')}
            title={fa('صفحات زندهٔ داشبورد', 'Live dashboard pages')}
            lead={
              fa(
                'همهٔ این صفحات به درگاه واقعی وصل‌اند؛ برای اجرای مدل‌ها (POST) وارد شوید. هر خروجی برچسب منشأ دارد.',
                'These pages connect to the real gateway; log in to run models (POST). Every output carries a provenance badge.'
              )
            }
          />
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { to: '/dashboard/monitoring', fa: 'پایش زمین (NDVI/ERA5)', en: 'Field monitoring (NDVI/ERA5)' },
              { to: '/dashboard/live/satellite', fa: 'ماهواره و اقلیم', en: 'Satellite & climate' },
              { to: '/dashboard/science-live', fa: 'زنجیرهٔ علمی زنده', en: 'Live scientific chain' },
              { to: '/dashboard/live/indices', fa: 'شاخص‌های هیدروما', en: 'HyDroMa indices' },
              { to: '/dashboard/live/soil', fa: 'خاک زنده', en: 'Live soil' },
              { to: '/dashboard/live/carbon', fa: 'کربن و MRV', en: 'Carbon & MRV' },
              { to: '/dashboard/economy', fa: 'اقتصاد (NPV/ROI)', en: 'Economy (NPV/ROI)' },
              { to: '/dashboard/live/et0', fa: 'تبخیر-تعرق (ET0)', en: 'ET0' },
              { to: '/dashboard/live/status', fa: 'وضعیت سرویس', en: 'Service status' },
              { to: '/dashboard/support', fa: 'پشتیبانی داشبورد', en: 'Dashboard support' },
              { to: '/dashboard/login', fa: 'ورود / ثبت‌نام', en: 'Login / Register' },
              { to: '/dashboard/profile', fa: 'پروفایل', en: 'Profile' },
            ].filter((card) => isAdmin || card.to !== '/dashboard/live/status').map((card) => (
              <Link
                key={card.to}
                to={card.to}
                className="glass glass-hover flex items-center gap-2.5 rounded-2xl px-4 py-3"
              >
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-leaf-400" aria-hidden />
                <span className="text-xs font-bold text-ink-2">{fa(card.fa, card.en)}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* portfolio */}
      <section className="px-4 py-10 sm:px-6" id="portfolio">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.portfolioTitle} lead={c.portfolioNote} />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {c.packages.map((pkg, index) => (
              <Reveal key={pkg.code} delay={(index % 3) * 0.06}>
                <SpotlightCard className="glass glass-hover flex h-full flex-col gap-2.5 rounded-3xl p-6">
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
                      <p className="text-[10px] text-emerald-100/40">{fa('بازگشت', 'Payback')}</p>
                      <p className="text-[11px] font-bold text-emerald-50">{pkg.payback}</p>
                    </div>
                  </div>
                  <p className="pt-1 text-[10px] leading-5 text-aqua-300/70">{pkg.keyModels}</p>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
