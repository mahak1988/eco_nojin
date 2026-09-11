import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import BaseCard, { type CardVariant } from '../components/dashboard/BaseCard';
import { useLang } from '../i18n/LanguageContext';
import { ussdGuide } from '../content/pages/guides';

export default function UssdGuidePage() {
  const { lang, t } = useLang();
  const c = ussdGuide[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/ussd-guide" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-10">
          <Reveal className="flex flex-col gap-4">
            <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.dialLabel}</h2>
            <code
              className="inline-block rounded-2xl bg-[var(--color-night-800)] px-6 py-4 text-3xl font-extrabold text-[var(--color-leaf-300)]"
              dir="ltr"
            >
              {c.dialCode}
            </code>
            <p className="text-sm leading-8 text-[var(--color-night-200)]">{c.menuIntro}</p>
          </Reveal>

          <section className="flex flex-col gap-5">
            <SectionHeading kicker={c.kicker} title={c.menuTitle} />
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {c.menuItems.map((item, index) => (
                <Reveal key={item.key} delay={index * 0.05}>
                  <BaseCard title={item.label} variant={(['leaf', 'sand', 'aqua', 'night'] as CardVariant[])[index % 4]}>
                    <div className="mt-2 flex items-start gap-3">
                      <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-leaf-500)] text-xs font-extrabold text-[var(--color-leaf-300)]">
                        {item.key}
                      </span>
                      <p className="text-xs leading-6 text-[var(--color-night-200)]">{item.desc}</p>
                    </div>
                  </BaseCard>
                </Reveal>
              ))}
            </div>
          </section>

          <section className="flex flex-col gap-5">
            <SectionHeading kicker={c.kicker} title={c.smsTitle} lead={c.smsLead} />
            <div className="grid gap-3 sm:grid-cols-2">
              {c.smsCommands.map((cmd, index) => (
                <Reveal key={cmd.cmd} delay={index * 0.05}>
                  <BaseCard title={cmd.cmd} variant="sand">
                    <p className="mt-2 text-xs leading-6 text-[var(--color-night-200)]">{cmd.desc}</p>
                  </BaseCard>
                </Reveal>
              ))}
            </div>
            <p className="text-xs text-[var(--color-night-200)]">{c.smsLimits}</p>
          </section>

          <section className="flex flex-col gap-3">
            <h3 className="text-sm font-extrabold text-[var(--color-sand-300)]">{c.tipsTitle}</h3>
            <ul className="flex flex-col gap-2.5">
              {c.tips.map((tip, index) => (
                <Reveal key={index} delay={index * 0.05}>
                  <li className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-aqua-400)]" aria-hidden />
                    {tip}
                  </li>
                </Reveal>
              ))}
            </ul>
          </section>
        </div>
      </section>
    </>
  );
}
