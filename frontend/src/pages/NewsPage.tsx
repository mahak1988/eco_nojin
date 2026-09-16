import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';

const CONTENT = {
  fa: {
    title: 'اخبار و به‌روزرسانی',
    kicker: 'اخبار',
    lead: 'رویدادها، نسخه‌های جدید و پیشرفت پروژه — شفاف و به‌روز.',
    items: [
      { date: '۱۴۰۵/۰۶/۲۵', title: 'راستی‌آزمایی کامل چرخه کشاورز تا فروش', body: 'سفر کامل کشاورز (ثبت‌نام، احیای زمین، برداشت، فروش در بازارگاه با اسکرو) روی پلتفرم زنده آزمایش و تأیید شد؛ ۴۶ از ۴۸ گام سبز و عیب‌های یافته مستند و در حال رفع است.' },
      { date: '۱۴۰۵/۰۶/۲۵', title: 'پایگاه دانش nojin بذرگیری شد', body: '۴۳ ماده احیایی مستند علمی، ۱۰ پروفایل خاک ایران و ۱۰ فرمولاسیون احیا به دانش‌پایه پلتفرم افزوده شد و اسکریپت رسمی بذرگیری به مخزن اضافه شد.' },
      { date: '۱۴۰۵/۰۶/۲۵', title: '۱۰ اقلیم، ۱۰ موفقیت', body: 'ده کاربر با شرایط کاملاً متفاوت اقلیمی (از کویر لوت تا جنگل‌های شمال) هر شش مرحله سفر علمی را با موفقیت کامل گذراندند.' },
    ],
  },
  en: {
    title: 'News & updates',
    kicker: 'News',
    lead: 'Events, releases and project progress — transparent and current.',
    items: [
      { date: '2026-09-16', title: 'Full farmer-to-sale cycle verified', body: 'The complete farmer journey (registration, land restoration, harvest, Bazargah sale with escrow) was tested on the live platform; 46 of 48 steps green, findings documented and fixes shipping.' },
      { date: '2026-09-16', title: 'Nojin knowledge base seeded', body: '43 scientifically documented restoration materials, 10 Iranian soil profiles and 10 formulation recipes were added, with an official seeding script in the repository.' },
      { date: '2026-09-16', title: '10 climates, 10 successes', body: 'Ten users across radically different climates (Lut desert to Hyrcanian forests) passed all six scientific journey stages.' },
    ],
  },
} as const;

export default function NewsPage() {
  const { lang } = useLang();
  const c = CONTENT[lang as 'fa' | 'en'];
  return (
    <>
      <Seo title={`${c.title} | Eco Nojin`} description={c.lead} path="/news" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto flex max-w-4xl flex-col gap-5">
          {c.items.map((n, i) => (
            <Reveal key={n.title} delay={i * 0.07}>
              <article className="glass rounded-3xl p-7">
                <time className="text-[11px] font-bold text-[var(--color-leaf-300)]">{n.date}</time>
                <h3 className="mt-1 text-base font-extrabold text-[var(--color-night-100)]">{n.title}</h3>
                <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/75">{n.body}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
