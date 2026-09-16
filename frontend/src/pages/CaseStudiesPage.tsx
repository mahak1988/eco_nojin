import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';

const CONTENT = {
  fa: {
    title: 'مطالعات موردی',
    kicker: 'شواهد میدانی',
    lead: 'نتایج واقعی احیای اکوسیستم با اکو نوژین — با اعداد، روش و راستی‌آزمایی.',
    cases: [
      {
        title: 'احیای ۵ هکتار زمین شور و بایر در اردکان یزد',
        body: 'زمین رهاشده با pH 8.3 و شوری 7.5 dS/m با فرمولاسیون NOJIN-ARID-2 (ژوت، گاورو، بایوچار، زئولیت، گوگرد) احیا شد. داشبورد هیدروما افزایش برداشت ۲۰۰٪ را پیش‌بینی کرد؛ برداشت محافظه‌کارانه ۱۷٬۵۰۰ کیلوگرم گندم برآورد شد و محصول با کد رهگیری در بازارگاه به فروش رسید و وجه آن با اسکرو تسویه شد.',
        metrics: ['+۲۰۰٪ پیش‌بینی برداشت', '۴۰٪ صرفه‌جویی آب', '۹۲/۱۰۰ کنترل کیفیت', 'اسکرو آزادشده'],
        tag: 'E2E راستی‌آزمایی‌شده روی پلتفرم زنده',
      },
      {
        title: 'مقیاس‌پذیری: ۱۰ اقلیم، ۱۰ خاک',
        body: '۱۰ پروفایل خاک از کویر لوت تا جنگل‌های خزری روی پلتفرم آزموده شد؛ هر ۱۰ کاربر فرمولاسیون اختصاصی، تحلیل اقتصادی و برنامه آبیاری دریافت کردند (۶۰/۶۰ گام موفق).',
        metrics: ['۱۰/۱۰ پروفایل موفق', 'از EC 0.8 تا 9.5 dS/m', 'pH 4.9 تا 9.1'],
        tag: 'آزمون مقیاس‌پذیری',
      },
    ],
  },
  en: {
    title: 'Case studies',
    kicker: 'Field evidence',
    lead: 'Real ecosystem-restoration results with Eco Nojin — numbers, method and verification.',
    cases: [
      {
        title: 'Restoring 5 ha of saline barren land in Ardakan, Yazd',
        body: 'Abandoned land (pH 8.3, EC 7.5 dS/m) was restored with the NOJIN-ARID-2 formulation (gypsum, sheep manure, biochar, zeolite, straw, sulfur). The HyDroMa dashboard projected a 200% yield uplift; a conservative 17,500 kg wheat harvest was estimated, the product sold in Bazargah with a traceability code, and funds settled via escrow.',
        metrics: ['+200% projected yield', '40% water savings', '92/100 quality score', 'Escrow released'],
        tag: 'E2E verified on the live platform',
      },
      {
        title: 'Scalability: 10 climates, 10 soils',
        body: 'Ten soil profiles from the Lut desert to Hyrcanian forests were tested on the platform; all 10 users received tailored formulations, economic analysis and irrigation plans (60/60 steps passed).',
        metrics: ['10/10 profiles passed', 'EC 0.8–9.5 dS/m', 'pH 4.9–9.1'],
        tag: 'Scalability test',
      },
    ],
  },
} as const;

export default function CaseStudiesPage() {
  const { lang } = useLang();
  const c = CONTENT[lang as 'fa' | 'en'];
  return (
    <>
      <Seo title={`${c.title} | Eco Nojin`} description={c.lead} path="/case-studies" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto flex max-w-5xl flex-col gap-6">
          <SectionHeading kicker={c.kicker} title={c.title} />
          {c.cases.map((cs, i) => (
            <Reveal key={cs.title} delay={i * 0.08}>
              <article className="glass rounded-3xl p-8">
                <span className="rounded-full bg-[var(--color-leaf-500)]/15 px-3 py-1 text-[11px] font-bold text-[var(--color-leaf-300)]">{cs.tag}</span>
                <h3 className="mt-3 text-lg font-extrabold text-[var(--color-night-100)]">{cs.title}</h3>
                <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/75">{cs.body}</p>
                <ul className="mt-4 flex flex-wrap gap-2">
                  {cs.metrics.map((m) => (
                    <li key={m} className="rounded-full border border-[var(--theme-border)] px-3 py-1 text-[11px] font-bold text-[var(--color-night-100)]">{m}</li>
                  ))}
                </ul>
              </article>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
