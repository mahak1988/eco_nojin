import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import { Link } from 'react-router-dom';

const CONTENT = {
  fa: {
    title: 'مرکز راهنما',
    kicker: 'راهنما',
    lead: 'پاسخ کوتاه سوال‌های رایج — و مسیر رسیدن به پاسخ کامل.',
    faqs: [
      { q: 'چطور زمین بایرم را ثبت کنم؟', a: 'پس از ثبت‌نام، از داشبورد بخش زمین، موقعیت و مساحت زمین را ثبت کنید؛ سپس تحلیل خاک و فرمولاسیون احیا را از هیدروما دریافت کنید.' },
      { q: 'در خشکسالی محصولم از بین نمی‌رود؟', a: 'پلتفرم شاخص‌های EWSI/HDVI و برنامه آبیاری دقیق EPIA را محاسبه می‌کند و فرمولاسیون احیا، نگه‌داشت آب خاک را تا ۵۰٪ افزایش می‌دهد.' },
      { q: 'چطور محصولم را بفروشم؟', a: 'از بازارگاه درخواست غرفه بدهید؛ پس از تأیید، محصول را با کد رهگیری ثبت کنید. وجه خریدار در اسکرو نگه‌داری و پس از تحویل آزاد می‌شود.' },
      { q: 'اینترنت ندارم، چطور استفاده کنم؟', a: 'راهنمای USSD برای مناطق کم‌اینترنت و راهنمای صوتی برای سواد دیجیتال محدود طراحی شده است.' },
    ],
    more: 'سوال دیگر دارید؟ صفحه پشتیبانی',
  },
  en: {
    title: 'Help center',
    kicker: 'Help',
    lead: 'Short answers to common questions — and the path to the full answer.',
    faqs: [
      { q: 'How do I register my barren land?', a: 'After signing up, open the Land section in the dashboard, add location and area, then get soil analysis and a restoration formulation from HyDroMa.' },
      { q: 'Will my crop survive drought?', a: 'The platform computes EWSI/HDVI drought indices and EPIA precision irrigation schedules; the restoration formulation raises soil water retention by up to 50%.' },
      { q: 'How do I sell my harvest?', a: 'Apply as a vendor in Bazargah; once approved, list products with a traceability code. Buyer funds are held in escrow and released after delivery.' },
      { q: 'I have no internet — can I still use it?', a: 'Yes: a USSD guide serves low-connectivity regions and a voice guide supports limited digital literacy.' },
    ],
    more: 'Need more? Visit support',
  },
} as const;

export default function HelpPage() {
  const { lang } = useLang();
  const c = CONTENT[lang as 'fa' | 'en'];
  return (
    <>
      <Seo title={`${c.title} | Eco Nojin`} description={c.lead} path="/help" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto flex max-w-4xl flex-col gap-4">
          {c.faqs.map((f, i) => (
            <Reveal key={f.q} delay={i * 0.06}>
              <div className="glass rounded-2xl p-6">
                <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{f.q}</h3>
                <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/75">{f.a}</p>
              </div>
            </Reveal>
          ))}
          <p className="mt-2 text-sm text-[var(--color-night-200)]/75">
            {c.more} — <Link to="/support" className="font-bold text-[var(--color-leaf-300)] hover:underline">{lang === 'fa' ? 'پشتیبانی' : 'Support'}</Link>
          </p>
        </div>
      </section>
    </>
  );
}
