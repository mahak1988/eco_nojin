import { Link } from 'react-router-dom';
import { ArrowLeft, FlaskConical } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';
import FieldScene from '../visuals/FieldScene';

/**
 * Hero v2 — golden-ratio split (61.8 / 38.2), one primary CTA + one text
 * link, and a slim 4-stat row. The old chip clutter is removed (report 66).
 */
export default function Hero() {
  const { t, dir, lang } = useLang();
  const isFa = lang === 'fa';
  const reduceMotion = useReducedMotion();
  const slimStats = t.stats.slice(0, 4);

  const fade = (delay: number) =>
    reduceMotion
      ? {}
      : {
          initial: { opacity: 0, y: 24 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.7, delay, ease: [0.22, 0.61, 0.36, 1] as const },
        };

  return (
    <section className="relative overflow-hidden px-4 pb-[55px] pt-[55px] sm:px-6 lg:pb-[89px] lg:pt-[89px]">
      <div className="mx-auto grid max-w-6xl items-center gap-[34px] lg:grid-cols-[1.618fr_1fr]">
        {/* copy — 61.8% */}
        <div className="flex flex-col items-start gap-[21px]">
          <motion.p {...fade(0)} className={isFa ? 'kicker kicker-fa' : 'kicker'}>
            {isFa ? 'پلتفرم علمی احیا و کشاورزی دقیق' : 'Restoration & precision farming science platform'}
          </motion.p>
          <motion.h1
            {...fade(0)}
            className="font-display text-[44px] font-semibold leading-[1.18] text-ink-1 sm:text-[58px] lg:text-[66px] lg:leading-[1.14]"
          >
            {t.hero.title} <span className="text-gradient-leaf text-shimmer">{t.hero.titleAccent}</span>
          </motion.h1>

          <motion.p {...fade(0.12)} className="max-w-xl text-base leading-[1.9] text-ink-2 sm:text-lg">
            {t.hero.subtitle}
          </motion.p>

          <motion.div {...fade(0.24)} className="flex flex-wrap items-center gap-[13px]">
            <Link
              to="/platform"
              className="ring-glow inline-flex items-center gap-2 rounded-full bg-leaf-500 px-[21px] py-3 text-sm font-extrabold text-night-950 transition-transform hover:scale-[1.03] active:scale-[0.98]"
            >
              {t.hero.ctaPrimary}
              <ArrowLeft className={`h-4 w-4 ${dir === 'rtl' ? '' : 'rotate-180'}`} aria-hidden />
            </Link>
            <Link
              to="/hydroma"
              className="inline-flex items-center gap-2 px-2 py-2 text-sm font-extrabold text-ink-2 transition-colors hover:text-leaf-300"
            >
              <FlaskConical className="h-4 w-4 text-aqua-400" aria-hidden />
              {t.hero.ctaSecondary}
            </Link>
          </motion.div>

          {/* slim 4-stat row (φ spacing, quiet dividers) */}
          <motion.dl
            {...fade(0.36)}
            className="mt-[13px] flex flex-wrap items-center gap-x-[34px] gap-y-[13px] border-t border-white/8 pt-[21px]"
          >
            {slimStats.map((stat) => (
              <div key={stat.label} className="flex flex-col gap-0.5">
                <dt className="font-tech order-2 text-[10px] uppercase tracking-[0.14em] text-ink-3">{stat.label}</dt>
                <dd className="font-display order-1 text-2xl font-semibold text-leaf-200">{stat.value}</dd>
              </div>
            ))}
          </motion.dl>
        </div>

        {/* visual — 38.2% */}
        <motion.div
          initial={reduceMotion ? undefined : { opacity: 0, scale: 0.96 }}
          animate={reduceMotion ? undefined : { opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 0.61, 0.36, 1] }}
        >
          <FieldScene />
        </motion.div>
      </div>
    </section>
  );
}
