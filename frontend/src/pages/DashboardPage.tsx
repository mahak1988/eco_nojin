/** HyDroMa science dashboard — 12-package portfolio + live model calculators. */

import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { dashboard } from '../content/pages/dashboard';
import {
  HortonCalculator,
  HydraulicsCalculator,
  RingCalculator,
  ScsCalculator,
  VgCalculator,
} from '../components/dashboard/calculators';

/** HyDroMa dashboard — prepared per the engineering booklets HP-01..HP-12. */
export default function DashboardPage() {
  const { lang, t } = useLang();
  const c = dashboard[lang as 'fa' | 'en'];

  const calcLabels = {
    horton: {
      title: lang === 'fa' ? 'نفوذ هورتون (HP-01/03 · F-01)' : 'Horton infiltration (HP-01/03 · F-01)',
      f0: 'نرخ اولیه',
      fc: 'نرخ نهایی',
      k: 'ضریب کاهش',
      duration: 'بازه',
      cumulative6: 'نفوذ تجمعی ۶ ساعت',
    },
    scs: {
      title: lang === 'fa' ? 'رواناب SCS-CN (HP-01/03 · F-02/03)' : 'SCS-CN runoff (HP-01/03 · F-02/03)',
      cn: 'شماره منحنی (CN)',
      retention: 'نگهداشت پتانسیل S',
      runoff50: 'رواناب برای بارش ۵۰ میلی‌متر',
      hydroGoal: 'هدف HP-01: کاهش CN',
    },
    vg: {
      title: lang === 'fa' ? 'منحنی رطوبت Van Genuchten (HP-01/06 · F-04)' : 'Van Genuchten retention (HP-01/06 · F-04)',
      thetaR: 'رطوبت پسماند θr',
      thetaS: 'رطوبت اشباع θs',
      alpha: 'پارامتر α',
      n: 'پارامتر n',
      thetaSat: 'θ نزدیک اشباع',
      awc: 'آب قابل دسترس (تقریبی)',
    },
    hydraulics: {
      title: lang === 'fa' ? 'هیدرولیک کانال مانینگ (HP-02 · F-02..F-08)' : 'Manning channel hydraulics (HP-02 · F-02..F-08)',
      manningN: 'ضریب زبری مانینگ n',
      area: 'سطح مقطع جریان A',
      perimeter: 'محیط خیس P',
      slope: 'شیب بستر S',
      hydraulicR: 'شعاع هیدرولیکی R',
      discharge: 'دبی Q',
      reynolds: 'عدد رینولدز',
      froude: 'عدد فرود',
      weirL: 'طول سرریز L',
      weirH: 'ارتفاع آب روی سرریز H',
      weirQ: 'دبی سرریز فرانسیس',
    },
    ring: {
      title: lang === 'fa' ? 'ذخیرهٔ حلقهٔ سنگی (HP-03 · F-01/02)' : 'Stone-ring storage (HP-03 · F-01/02)',
      radius: 'شعاع حلقه r',
      depth: 'عمق پرشدگی h',
      nEff: 'تخلخل مؤثر n_eff',
      storage: 'حجم ذخیره',
      darcy: 'نفوذ دارسی (تقریبی)',
    },
  };

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
