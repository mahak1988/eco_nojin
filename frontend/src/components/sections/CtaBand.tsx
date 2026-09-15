import { Link } from 'react-router-dom';
import { Mail, LogIn } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

/** Final call-to-action band shown at the bottom of every page. */
export default function CtaBand() {
  const { t, lang } = useLang();

  return (
    <section className="px-4 pb-4 pt-10 sm:px-6">
      <Reveal className="mx-auto max-w-6xl">
        <div className="ring-glow flex flex-col items-center gap-5 rounded-[2.5rem] bg-gradient-to-b from-leaf-600/25 to-night-900 px-6 py-14 text-center sm:px-12">
          <h2 className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">{t.cta.title}</h2>
          <p className="max-w-xl text-base leading-8 text-[var(--color-night-200)]/65">{t.cta.lead}</p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/about"
              className="inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-7 py-3.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.04] active:scale-[0.98]"
            >
              <Mail className="h-4 w-4" aria-hidden />
              {t.cta.button}
            </Link>
            <Link
              to="/login"
              className="glass glass-hover inline-flex items-center gap-2 rounded-full border border-[var(--color-leaf-500)]/40 bg-[var(--color-leaf-500)]/10 px-7 py-3.5 text-sm font-extrabold text-[var(--color-leaf-300)] transition-transform hover:scale-[1.04] active:scale-[0.98]"
            >
              <LogIn className="h-4 w-4" aria-hidden />
              {lang === 'fa' ? 'ورود' : 'Login'}
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
