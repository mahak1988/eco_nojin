import { useLang } from '../../i18n/LanguageContext';
import { Calendar } from 'lucide-react';
import Reveal from '../ui/Reveal';

interface EventItem {
  date: string;
  title: string;
  desc: string;
}

const EVENTS_FA: EventItem[] = [
  { date: 'آبان ۱۴۰۵', title: 'کارگاه مدل‌سازی هیدروما', desc: 'آموزش عملی مدل‌های ریچاردز و سنت‌ونان برای کشاورزان.' },
  { date: 'آذر ۱۴۰۵', title: 'همایش بین‌المللی احیای اکوسیستم', desc: 'ارائه نتایج پروژه‌های پایش ماهواره‌ای.' },
  { date: 'دی ۱۴۰۵', title: 'راه‌اندازی بازارگاه کربن', desc: 'عرضه اولین اعتبارهای کربن تأییدشده روی پلتفرم.' },
];

const EVENTS_EN: EventItem[] = [
  { date: 'Nov 2026', title: 'HyDroMa Modeling Workshop', desc: 'Hands-on training on Richards and Saint-Venant models.' },
  { date: 'Dec 2026', title: 'Ecosystem Restoration Summit', desc: 'Presenting satellite monitoring project results.' },
  { date: 'Jan 2027', title: 'Carbon Marketplace Launch', desc: 'First verified carbon credits listed on platform.' },
];

/** Upcoming events cards. */
export default function EventCards() {
  const { lang } = useLang();
  const events = lang === 'fa' ? EVENTS_FA : EVENTS_EN;

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="events" aria-labelledby="events-heading">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 flex items-center gap-3">
            <Calendar className="h-5 w-5 text-[var(--color-sand-400)]" aria-hidden />
            <p className="text-sm font-extrabold text-[var(--color-sand-400)]">{lang === 'fa' ? 'رویدادها' : 'Events'}</p>
          </div>
          <h2 id="events-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
            {lang === 'fa' ? 'در انتظار شما' : 'Upcoming'}
          </h2>

          <div className="mt-8 flex flex-col gap-3">
            {events.map((event, index) => (
              <Reveal key={event.title} delay={index * 0.08}>
                <div className="flex items-start gap-4 rounded-3xl glass p-5">
                  <div className="flex flex-col items-center min-w-[64px]">
                    <span className="text-xs font-bold text-[var(--color-sand-300)]">{event.date.split(' ')[0]}</span>
                    <span className="text-lg font-extrabold text-[var(--color-night-100)]">{event.date.split(' ').slice(1).join(' ')}</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{event.title}</h3>
                    <p className="text-sm leading-6 text-[var(--color-night-200)]/60">{event.desc}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </Reveal>
  );
}
