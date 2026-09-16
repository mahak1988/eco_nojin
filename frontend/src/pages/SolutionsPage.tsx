import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { Link } from 'react-router-dom';
import { useLang } from '../i18n/LanguageContext';

const CONTENT = {
  fa: {
    title: 'راهکارها برای هر نقش',
    kicker: 'راهکارها',
    lead: 'یک پلتفرم، چهار مخاطب: کشاورز، پژوهشگر، سازمان و سرمایه‌گذار — برای هر یک مسیر ارزش مشخصی طراحی شده است.',
    audiences: [
      { title: 'کشاورز و بهره‌بردار', desc: 'ثبت زمین بایر، دریافت فرمولاسیون احیای خاک از داشبورد علمی هیدروما، برنامه آبیاری دقیق در خشکسالی، و فروش تضمینی محصول در بازارگاه با کد رهگیری و اسکرو.', cta: 'شروع سفر کشاورز', to: '/register' },
      { title: 'پژوهشگر و دانشگاه', desc: 'دسترسی به موتورهای علمی (FAO-56، RothC، RUSLE، Richards)، داده‌های ماهواره‌ای و API باز برای پژوهش‌های آب، خاک و کربن.', cta: 'موتورهای علمی', to: '/hydroma' },
      { title: 'سازمان و دولت محلی', desc: 'پایش احیای سرزمین در مقیاس حوضه، داشبورد MRV برای گزارش‌دهی کربن، و مدیریت پروژه‌های مشارکت محلی.', cta: 'گفت‌وگو با ما', to: '/contact' },
      { title: 'سرمایه‌گذار و حامی', desc: 'مدل اقتصادی شفاف (ROI/NPV/IRR برای هر پروژه)، توکن‌سازی اعتبار کربن و گزارش تاثیر اجتماعی.', cta: 'اطلاعات سرمایه‌گذاری', to: '/investors' },
    ],
  },
  en: {
    title: 'Solutions for every role',
    kicker: 'Solutions',
    lead: 'One platform, four audiences: farmer, researcher, organization and investor — each with a clear value path.',
    audiences: [
      { title: 'Farmer & Producer', desc: 'Register barren land, get a science-based soil restoration formulation from the HyDroMa dashboard, precise irrigation under drought, and guaranteed sales in Bazargah with traceability and escrow.', cta: 'Start the farmer journey', to: '/register' },
      { title: 'Researcher & Academia', desc: 'Access scientific engines (FAO-56, RothC, RUSLE, Richards), satellite data pipelines and an open API for water, soil and carbon research.', cta: 'Scientific engines', to: '/hydroma' },
      { title: 'Organization & Local Government', desc: 'Watershed-scale restoration monitoring, an MRV dashboard for carbon reporting, and community project management.', cta: 'Talk to us', to: '/contact' },
      { title: 'Investor & Supporter', desc: 'Transparent economics (ROI/NPV/IRR per project), carbon-credit tokenization and social-impact reporting.', cta: 'Investor information', to: '/investors' },
    ],
  },
} as const;

export default function SolutionsPage() {
  const { lang } = useLang();
  const c = CONTENT[lang as 'fa' | 'en'];
  return (
    <>
      <Seo title={`${c.title} | Eco Nojin`} description={c.lead} path="/solutions" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <SectionHeading kicker={c.kicker} title={c.title} />
          <div className="grid gap-4 md:grid-cols-2">
            {c.audiences.map((a, i) => (
              <Reveal key={a.title} delay={i * 0.07}>
                <div className="glass glass-hover h-full rounded-3xl p-7">
                  <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{a.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/75">{a.desc}</p>
                  <Link to={a.to} className="mt-4 inline-block rounded-full bg-[var(--color-leaf-500)] px-5 py-2 text-xs font-extrabold text-[var(--color-night-950)]">
                    {a.cta}
                  </Link>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
