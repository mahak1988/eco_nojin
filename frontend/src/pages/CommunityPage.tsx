import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';

const CONTENT = {
  fa: {
    title: 'انجمن و مشارکت',
    kicker: 'انجمن',
    lead: 'اکو نوژین یک پروژه متن‌باز و محور-محلی است؛ جای شما اینجاست.',
    ways: [
      { title: 'توسعه‌دهنده', desc: 'مخزن متن‌باز (MIT): بک‌اند FastAPI، فرانت React 19، موتور علمی C++20/Python. مسائل خوب برای شروع با برچسب good-first-issue.' },
      { title: 'علم داده و مزرعه', desc: 'داده مزرعه‌ای، راستی‌آزمایی میدانی فرمولاسیون‌ها و بازخورد واقعی کشاورزان ارزشمندترین بخش چرخه ماست.' },
      { title: 'ترجمه و آموزش', desc: 'مستندات دوزبانه فارسی/انگلیسی و راهنماهای صوتی محلی نیاز به ویراستار و گوینده دارد.' },
      { title: 'انجمن محلی', desc: 'در روستای پایلوت یا از راه دور: آموزش کشاورزان، جمع‌آوری داده با KoboToolbox و پشتیبانی USSD.' },
    ],
  },
  en: {
    title: 'Community & contributing',
    kicker: 'Community',
    lead: 'Eco Nojin is open source (MIT) and locally rooted — there is a place for you.',
    ways: [
      { title: 'Developer', desc: 'Open-source repo: FastAPI backend, React 19 frontend, C++20/Python scientific engine. good-first-issue labels mark starting points.' },
      { title: 'Data & agronomy', desc: 'On-farm data, field validation of formulations and real farmer feedback are the most valuable part of our loop.' },
      { title: 'Translation & education', desc: 'Bilingual fa/en docs and local voice guides need editors and narrators.' },
      { title: 'Local community', desc: 'In the pilot village or remote: farmer training, KoboToolbox data collection and USSD support.' },
    ],
  },
} as const;

export default function CommunityPage() {
  const { lang } = useLang();
  const c = CONTENT[lang as 'fa' | 'en'];
  return (
    <>
      <Seo title={`${c.title} | Eco Nojin`} description={c.lead} path="/community" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto grid max-w-6xl gap-4 md:grid-cols-2">
          {c.ways.map((w, i) => (
            <Reveal key={w.title} delay={i * 0.07}>
              <div className="glass glass-hover h-full rounded-3xl p-7">
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{w.title}</h3>
                <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/75">{w.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
