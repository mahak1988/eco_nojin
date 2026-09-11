import { Link } from 'react-router-dom';
import { ArrowLeft, FlaskConical } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';
import FieldScene from '../visuals/FieldScene';

/** Landing hero: headline + CTAs on one side, satellite field scene on the other. */
export default function Hero() {
  const { t, lang, dir } = useLang();
  const reduceMotion = useReducedMotion();

  const fade = (delay: number) =>
    reduceMotion
      ? {}
      : {
          initial: { opacity: 0, y: 24 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.7, delay, ease: [0.22, 0.61, 0.36, 1] as const },
        };

  return (
    <section className="relative overflow-hidden px-4 pb-20 pt-14 sm:px-6 lg:pb-28 lg:pt-20">
      <div className="mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-[1.05fr_0.95fr]">
        {/* copy */}
        <div className="flex flex-col items-start gap-6">
          <motion.span
            {...fade(0)}
            className="glass inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-bold text-[var(--color-leaf-300)]"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-leaf-400)] animate-pulse-soft" aria-hidden />
            {t.hero.kicker}
          </motion.span>

          <motion.h1
            {...fade(0.12)}
            className="text-4xl font-extrabold leading-[1.25] text-[var(--color-night-100)] sm:text-5xl lg:text-[3.4rem] lg:leading-[1.2]"
          >
            {t.hero.title}{' '}
            <span className="text-gradient-leaf text-shimmer">{t.hero.titleAccent}</span>
          </motion.h1>

          <motion.p
            {...fade(0.24)}
            className="max-w-xl text-base leading-8 text-[var(--color-night-200)]/65 sm:text-lg sm:leading-9"
          >
            {t.hero.subtitle}
          </motion.p>

          <motion.div {...fade(0.36)} className="flex flex-wrap items-center gap-3">
            <Link
              to="/platform"
              className="ring-glow inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-6 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03] active:scale-[0.98]"
            >
              {t.hero.ctaPrimary}
              {dir === 'rtl' ? (
                <ArrowLeft className="h-4 w-4" aria-hidden />
              ) : (
                <ArrowLeft className="h-4 w-4 rotate-180" aria-hidden />
              )}
            </Link>
            <Link
              to="/hydroma"
              className="glass glass-hover inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-extrabold text-[var(--color-night-100)]"
            >
              <FlaskConical className="h-4 w-4 text-[var(--color-aqua-300)]" aria-hidden />
              {t.hero.ctaSecondary}
            </Link>
          </motion.div>

          <motion.p {...fade(0.48)} className="text-xs text-[var(--color-night-200)]/40" dir={lang === 'fa' ? 'ltr' : 'rtl'}>
            {lang === 'fa' ? 'HyDroMa · Sentinel-2 · ERA5 · Polygon' : 'هیدروما · سنتینل-۲ · ERA5 · پالیگون'}
          </motion.p>
        </div>

        {/* visual */}
        <motion.div
          initial={reduceMotion ? undefined : { opacity: 0, scale: 0.94 }}
          animate={reduceMotion ? undefined : { opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 0.61, 0.36, 1] }}
        >
          <FieldScene />
        </motion.div>
      </div>
    </section>
  );
}
