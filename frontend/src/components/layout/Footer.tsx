import { useState, type FormEvent } from 'react';
import { Globe, Mail, Send } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLang } from '../../i18n/LanguageContext';
import Logo from '../visuals/Logo';
import { footerGroups, legalGroup } from '../../content/menus';
import { subscribeNewsletter } from '../../lib/api';

interface Accent {
  text: string;
  softBg: string;
  border: string;
  dot: string;
  hoverText: string;
}

/** Per-category accent colors — stable order in content/menus.ts. */
const accents: Accent[] = [
  { text: 'text-leaf-300', softBg: 'bg-leaf-500/10', border: 'border-leaf-500/30', dot: 'bg-leaf-400', hoverText: 'hover:text-leaf-300' },
  { text: 'text-aqua-300', softBg: 'bg-aqua-500/10', border: 'border-aqua-500/30', dot: 'bg-aqua-400', hoverText: 'hover:text-aqua-300' },
  { text: 'text-sand-300', softBg: 'bg-sand-500/10', border: 'border-sand-500/30', dot: 'bg-sand-400', hoverText: 'hover:text-sand-300' },
  { text: 'text-violet-300', softBg: 'bg-violet-400/10', border: 'border-violet-400/30', dot: 'bg-violet-300', hoverText: 'hover:text-violet-300' },
];

/** Redesigned footer: brand+newsletter band, four tinted category cards
 * and a legal bar — tidy boxes, one accent color per category. */
export default function Footer() {
  const { t, lang } = useLang();
  const groups = footerGroups[lang as 'fa' | 'en'];
  const legal = legalGroup[lang as 'fa' | 'en'];

  const [email, setEmail] = useState('');
  const [newsStatus, setNewsStatus] = useState<'idle' | 'sending' | 'ok' | 'error'>('idle');

  const handleNewsletter = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setNewsStatus('error');
      return;
    }
    setNewsStatus('sending');
    try {
      await subscribeNewsletter(email, lang);
      setNewsStatus('ok');
      setEmail('');
    } catch (error) {
      console.error('Newsletter subscription failed', error);
      setNewsStatus('error');
    }
  };

  const newsLabels = {
    title: lang === 'fa' ? 'خبرنامه پروژه' : 'Project newsletter',
    hint: lang === 'fa' ? 'گزارش پیشرفت، پایلوت و داده‌های باز — کم‌تکرار.' : 'Progress, pilot and open data — rarely sent.',
    placeholder: lang === 'fa' ? 'ایمیل شما' : 'Your email',
    button: lang === 'fa' ? 'عضویت' : 'Subscribe',
    ok: lang === 'fa' ? 'عضو شدید؛ سپاس!' : 'Subscribed — thanks!',
    error: lang === 'fa' ? 'عضویت ناموفق؛ دوباره تلاش کنید.' : 'Subscription failed — try again.',
  };

  return (
    <footer className="relative mt-24 border-t border-white/8">
      <div className="mx-auto max-w-6xl px-4 pt-14 sm:px-6">
        {/* band: brand + newsletter */}
        <div className="glass mb-6 grid gap-8 rounded-[2rem] p-7 sm:p-9 lg:grid-cols-[1.35fr_1fr] lg:items-center">
          <div className="flex flex-col gap-4">
            <Logo wordmark={t.brand.name} size={44} />
            <p className="max-w-md text-sm leading-7 text-emerald-100/55">{t.footer.desc}</p>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
              <a
                href={`mailto:${t.about.email}`}
                className="inline-flex items-center gap-2 text-sm text-emerald-100/60 transition-colors hover:text-leaf-300"
                dir="ltr"
              >
                <Mail className="h-4 w-4 shrink-0 text-leaf-400/80" aria-hidden />
                {t.about.email}
              </a>
              <span className="inline-flex items-center gap-2 text-sm text-emerald-100/60" dir="ltr">
                <Globe className="h-4 w-4 shrink-0 text-leaf-400/80" aria-hidden />
                {t.about.site}
              </span>
            </div>
          </div>

          <form
            onSubmit={handleNewsletter}
            className="rounded-3xl border border-aqua-500/25 bg-aqua-500/8 p-6"
            aria-label={newsLabels.title}
          >
            <h3 className="text-sm font-extrabold text-aqua-200">{newsLabels.title}</h3>
            <p className="mt-1 text-[11px] leading-5 text-emerald-100/50">{newsLabels.hint}</p>
            <div className="mt-4 flex gap-2">
              <input
                type="email"
                dir="ltr"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={newsLabels.placeholder}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-xs text-emerald-50 placeholder:text-emerald-100/30 focus:border-aqua-400/60 focus:outline-none"
                required
              />
              <button
                type="submit"
                disabled={newsStatus === 'sending'}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-xl bg-aqua-400 px-4 py-2.5 text-xs font-extrabold text-night-950 transition-transform hover:scale-[1.03] disabled:opacity-60"
              >
                <Send className="h-3.5 w-3.5" aria-hidden />
                {newsLabels.button}
              </button>
            </div>
            {newsStatus === 'ok' ? (
              <p className="mt-2 text-[11px] font-bold text-leaf-300">{newsLabels.ok}</p>
            ) : null}
            {newsStatus === 'error' ? (
              <p role="alert" className="mt-2 text-[11px] font-bold text-red-300">
                {newsLabels.error}
              </p>
            ) : null}
          </form>
        </div>

        {/* category cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {groups.map((group, index) => {
            const accent = accents[index % accents.length];
            const multiColumn = group.links.length > 5;
            return (
              <nav
                key={group.title}
                aria-label={group.title}
                className={`glass glass-hover flex h-full flex-col gap-4 rounded-3xl border p-6 ${accent.border} ${accent.softBg}`}
              >
                <h3 className={`flex items-center gap-2 text-sm font-extrabold ${accent.text}`}>
                  <span className={`h-2 w-2 rounded-full ${accent.dot}`} aria-hidden />
                  {group.title}
                </h3>
                <div
                  className={
                    multiColumn
                      ? 'grid grid-cols-2 gap-x-3 gap-y-1'
                      : 'flex flex-col items-start gap-1'
                  }
                >
                  {group.links.map((link) => (
                    <Link
                      key={link.to}
                      to={link.to}
                      className={`w-fit rounded-lg px-2 py-1 text-[13px] text-emerald-100/65 transition-colors hover:bg-white/5 ${accent.hoverText}`}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              </nav>
            );
          })}
        </div>

        {/* legal bar */}
        <div className="mt-6 flex flex-col items-center gap-4 rounded-3xl border border-white/8 bg-white/3 px-6 py-5 sm:flex-row sm:justify-between">
          <nav aria-label={legal.title} className="flex flex-wrap items-center justify-center gap-x-1 gap-y-1">
            {legal.links.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="rounded-full px-3.5 py-1.5 text-xs text-emerald-100/55 transition-colors hover:bg-white/5 hover:text-leaf-300"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <p className="text-center text-xs text-emerald-100/35">{t.footer.legal}</p>
        </div>
      </div>
    </footer>
  );
}
