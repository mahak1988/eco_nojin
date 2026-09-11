import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCcw, Share2, User, Settings } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import UniversalCard from '../components/ui/UniversalCard';
import type { CardTheme } from '../components/ui/UniversalCard';
import CategoryTree from '../components/dashboard/CategoryTree';
import { useLang } from '../i18n/LanguageContext';
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

const PACKAGE_THEMES: Record<string, CardTheme> = {

  'HP-01': 'leaf',
  'HP-02': 'aqua',
  'HP-03': 'sand',
  'HP-04': 'leaf',
  'HP-05': 'aqua',
  'HP-06': 'sand',
  'HP-07': 'leaf',
  'HP-08': 'aqua',
  'HP-09': 'sand',
  'HP-10': 'leaf',
  'HP-11': 'aqua',
  'HP-12': 'sand',
};

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
          <p className="text-center text-[11px] text-[var(--color-night-200)]/35">{c.calcNote}</p>
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
            <Link to="/dashboard/profile" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold text-[var(--color-night-200)]/70">
              <User className="h-3.5 w-3.5" aria-hidden />
              {lang === 'fa' ? 'پروفایل' : 'Profile'}
            </Link>
            <Link to="/dashboard/settings" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold text-[var(--color-night-200)]/70">
              <Settings className="h-3.5 w-3.5" aria-hidden />
              {lang === 'fa' ? 'تنظیمات' : 'Settings'}
            </Link>
          </div>
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={loadRuns}
              className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-extrabold text-[var(--color-night-100)]"
            >
              <RefreshCcw className="h-3.5 w-3.5" aria-hidden />
              {lang === 'fa' ? 'به‌روزرسانی' : 'Refresh'}
            </button>
            <span className="text-[11px] text-[var(--color-night-200)]/35">
              {lang === 'fa' ? `${runs.length} اجرا` : `${runs.length} runs`}
            </span>
          </div>

          {hubState === 'loading' ? (
            <p className="glass rounded-2xl p-5 text-center text-sm text-[var(--color-night-200)]/55">
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
            <p className="glass rounded-2xl p-5 text-center text-sm text-[var(--color-night-200)]/55">
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
                    <p className="text-sm font-extrabold text-[var(--color-night-100)]" dir="ltr">
                      {run.title ?? run.model_id}
                    </p>
                    <p className="text-[11px] text-[var(--color-night-200)]/45" dir="ltr">
                      {run.model_id} · {run.created_at?.slice(0, 16).replace('T', ' ')}
                    </p>
                  </div>
                  {run.shared ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-leaf-500)]/15 px-3 py-1 text-[10px] font-bold text-[var(--color-leaf-300)]">
                      <Share2 className="h-3 w-3" aria-hidden />
                      {lang === 'fa' ? 'اشتراک عمومی' : 'Shared'}
                    </span>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => toggleShare(run)}
                    className="glass glass-hover rounded-full px-3.5 py-1.5 text-[11px] font-bold text-[var(--color-night-200)]/70"
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

      {/* model registry stats */}
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

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Reveal delay={0.1}>
              <UniversalCard
                title={String(registryStats.total)}
                desc={lang === 'fa' ? 'مدل ثبت‌شده' : 'registered models'}
                theme="leaf"
                icon="blocks"
                flipOnHover={false}
              />
            </Reveal>
            <Reveal delay={0.12}>
              <UniversalCard
                title={String(registryStats.calculators)}
                desc={lang === 'fa' ? 'محاسبه‌گر داشبورد' : 'dashboard calculators'}
                theme="aqua"
                icon="flask"
                flipOnHover={false}
              />
            </Reveal>
            <Reveal delay={0.14}>
              <UniversalCard
                title={String(registryStats.engine)}
                desc={lang === 'fa' ? 'موتور بک‌اند' : 'backend engines'}
                theme="sand"
                icon="server"
                flipOnHover={false}
              />
            </Reveal>
          </div>

          {/* categorized model tree */}
          <CategoryTree />
        </div>
      </section>

      {/* portfolio */}
      <section className="px-4 py-10 sm:px-6" id="portfolio">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.portfolioTitle} lead={c.portfolioNote} />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {c.packages.map((pkg, index) => (
              <Reveal key={pkg.code} delay={(index % 3) * 0.06}>
                <UniversalCard
                  title={lang === 'fa' ? pkg.title : pkg.titleEn}
                  desc={pkg.desc}
                  unit={pkg.code}
                  icon="leaf"
                  theme={PACKAGE_THEMES[pkg.code] || 'leaf'}
                  index={index}
                  flipOnHover={true}
                  backContent={{
                    source: lang === 'fa' ? pkg.keyModels : pkg.keyModels,
                    method: pkg.priority,
                    standard: pkg.capex,
                    frequency: lang === 'fa' ? pkg.payback : pkg.payback,
                    apiField: pkg.code,
                  }}
                />
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
