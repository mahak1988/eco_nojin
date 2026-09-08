import { Link } from 'react-router-dom';
import { CheckCircle2 } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

/** Carbon / MRV highlight band with gradient border. */
export default function CarbonBand() {
  const { t } = useLang();

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-20" id="carbon">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <div className="relative overflow-hidden rounded-[2.5rem] border border-leaf-500/20 bg-gradient-to-br from-night-800 via-night-900 to-night-950 p-8 sm:p-12">
            {/* decorative glow */}
            <div
              className="absolute -top-24 end-[-8%] h-72 w-72 rounded-full opacity-25 blur-[100px]"
              style={{ background: 'radial-gradient(circle, #d49b3f 0%, transparent 70%)' }}
              aria-hidden
            />
            <div
              className="absolute -bottom-24 start-[-6%] h-72 w-72 rounded-full opacity-25 blur-[100px]"
              style={{ background: 'radial-gradient(circle, #2fb36b 0%, transparent 70%)' }}
              aria-hidden
            />

            <div className="relative grid gap-10 lg:grid-cols-[1.1fr_1fr] lg:items-center">
              <div className="flex flex-col gap-4">
                <span className="inline-flex w-fit items-center gap-2 rounded-full border border-sand-500/30 bg-sand-500/10 px-4 py-1 text-xs font-bold text-sand-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-sand-400 animate-pulse-soft" aria-hidden />
                  {t.carbon.kicker}
                </span>
                <h2 className="text-3xl font-extrabold leading-snug text-emerald-50 sm:text-4xl">
                  {t.carbon.title}
                </h2>
                <p className="max-w-lg text-base leading-8 text-emerald-100/60">{t.carbon.lead}</p>
              </div>

              <ul className="flex flex-col gap-3">
                {t.carbon.bullets.map((bullet, index) => (
                  <Reveal key={bullet} delay={index * 0.08}>
                    <li className="glass flex items-start gap-3 rounded-2xl p-4">
                      <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-leaf-400" aria-hidden />
                      <span className="text-sm leading-7 text-emerald-50/85">{bullet}</span>
                    </li>
                  </Reveal>
                ))}
              </ul>

              <Link
                to="/carbon"
                className="mt-2 inline-flex w-fit items-center gap-2 rounded-full bg-leaf-500/15 px-5 py-2.5 text-xs font-extrabold text-leaf-300 transition-transform hover:scale-[1.03]"
              >
                {t.carbon.cta}
              </Link>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
