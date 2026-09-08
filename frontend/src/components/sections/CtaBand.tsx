import { Link } from 'react-router-dom';
import { Mail } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

/** Final call-to-action band shown at the bottom of every page. */
export default function CtaBand() {
  const { t } = useLang();

  return (
    <section className="px-4 pb-4 pt-10 sm:px-6">
      <Reveal className="mx-auto max-w-6xl">
        <div className="ring-glow flex flex-col items-center gap-5 rounded-[2.5rem] bg-gradient-to-b from-leaf-600/25 to-night-900 px-6 py-14 text-center sm:px-12">
          <h2 className="text-3xl font-extrabold text-emerald-50 sm:text-4xl">{t.cta.title}</h2>
          <p className="max-w-xl text-base leading-8 text-emerald-100/65">{t.cta.lead}</p>
          <Link
            to="/about"
            className="inline-flex items-center gap-2 rounded-full bg-leaf-500 px-7 py-3.5 text-sm font-extrabold text-night-950 transition-transform hover:scale-[1.04] active:scale-[0.98]"
          >
            <Mail className="h-4 w-4" aria-hidden />
            {t.cta.button}
          </Link>
        </div>
      </Reveal>
    </section>
  );
}
