import { FileCheck2 } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

/** Concrete decision-grade outputs of the scientific chain. */
export default function OutputsList() {
  const { t } = useLang();

  return (
    <section className="px-4 py-14 sm:px-6" id="outputs">
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <SectionHeading
          kicker={t.science.kicker}
          title={t.science.outputsTitle}
          lead={t.science.outputsLead}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          {t.science.outputs.map((output, index) => (
            <Reveal key={output} delay={index * 0.06}>
              <div className="glass glass-hover flex h-full items-start gap-4 rounded-2xl p-6">
                <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--color-leaf-500)]/12 text-[var(--color-leaf-300)]">
                  <FileCheck2 className="h-5 w-5" aria-hidden />
                </span>
                <p className="text-sm leading-7 text-[var(--color-night-100)]/85">{output}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
