import { useLang } from '../../i18n/LanguageContext';
import { Quote } from 'lucide-react';
import Reveal from '../ui/Reveal';

interface Testimonial {
  name: string;
  role: string;
  quote: string;
  organization: string;
}

const TESTIMONIALS_FA: Testimonial[] = [
  {
    name: 'دکتر سارا مهرپور',
    role: 'مدیر مرکز تحقیقات کشاورزی',
    quote: 'پلتفرم اکو نوژین داده‌های ماهواره‌ای را به ابزارهای عملی تبدیل می‌کند. این یک پیشرفت بزرگ برای کشاورزان ایران است.',
    organization: 'مؤسسه تحقیقات کشاورزی',
  },
  {
    name: 'رضا کریمی',
    role: 'کشاورز پایدار',
    quote: 'با استفاده از پیش‌بینی‌های هیدروما، مصرف آب مزرعه ما ۳۰٪ کاهش پیدا کرد. نتیجه واقعی و قابل اندازه‌گیری است.',
    organization: 'مزرعه سبز کویر',
  },
  {
    name: 'مریم رضایی',
    role: 'مشاور تغییرات اقلیمی',
    quote: 'شفافیت MRV اکو نوژین باعث شده خریداران اعتبار کربن مطمئن‌ترین تصمیم‌ها را داشته باشند.',
    organization: 'سازمان محیط زیست',
  },
];

const TESTIMONIALS_EN: Testimonial[] = [
  {
    name: 'Dr. Sara Mehripour',
    role: 'Agricultural Research Director',
    quote: 'Eco Nojin transforms satellite data into practical tools. A major leap forward for Iranian agriculture.',
    organization: 'Agricultural Research Institute',
  },
  {
    name: 'Reza Karimi',
    role: 'Sustainable Farmer',
    quote: 'With HyDroMa predictions, our farm water usage dropped 30%. Real, measurable results.',
    organization: 'Gavaznbaf Farm',
  },
  {
    name: 'Maryam Rezaei',
    role: 'Climate Change Consultant',
    quote: 'Eco Nojin\'s MRV transparency gives carbon credit buyers confidence in their decisions.',
    organization: 'Environment Organization',
  },
];

/** Testimonial cards with quotes. */
export default function Testimonials() {
  const { lang } = useLang();
  const testimonials = lang === 'fa' ? TESTIMONIALS_FA : TESTIMONIALS_EN;

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="testimonials" aria-labelledby="testimonials-heading">
      <div className="mx-auto max-w-6xl">
        <p className="mb-2 text-center text-sm font-extrabold text-[var(--color-leaf-400)]">{lang === 'fa' ? 'نظرات' : 'Testimonials'}</p>
        <h2 id="testimonials-heading" className="mb-12 text-center text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
          {lang === 'fa' ? 'باور کننده‌ها' : 'Who Trust Us'}
        </h2>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((t, index) => (
            <Reveal key={t.name} delay={index * 0.08}>
              <blockquote className="relative flex flex-col gap-4 rounded-3xl glass p-6">
                <Quote className="h-8 w-8 shrink-0 text-[var(--color-leaf-500)]/30" aria-hidden />
                <p className="text-sm leading-7 text-[var(--color-night-100)]/85">{t.quote}</p>
                <footer className="mt-auto pt-4 border-t border-white/10">
                  <p className="text-sm font-extrabold text-[var(--color-night-100)]">{t.name}</p>
                  <p className="text-xs text-[var(--color-night-200)]/50">{t.role} · {t.organization}</p>
                </footer>
              </blockquote>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
