import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface PageHeaderProps {
  kicker: string;
  title: string;
  lead: string;
}

/** Shared top block for inner pages — editorial display title, mono kicker
 * with gold accent, and a gradient hairline (Design-Horizons upgrade). */
export default function PageHeader({ kicker, title, lead }: PageHeaderProps) {
  const { lang } = useLang();

  return (
    <section className="px-4 pb-8 pt-14 sm:px-6 lg:pt-20">
      <Reveal className="mx-auto flex max-w-6xl flex-col items-start gap-4">
        <p className={`kicker flex items-center gap-3 ${lang === 'fa' ? 'kicker-fa' : ''}`}>
          <span className="inline-block h-px w-8 bg-[var(--color-sand-400)]/60" aria-hidden />
          {kicker}
        </p>
        <h1 className="font-display max-w-3xl text-4xl font-semibold leading-[1.18] text-[var(--color-night-100)] sm:text-6xl">
          {title}
        </h1>
        <p
          className={`max-w-2xl text-base leading-8 text-[var(--color-night-200)]/60 ${
            lang === 'fa' ? 'sm:text-lg sm:leading-9' : ''
          }`}
        >
          {lead}
        </p>
        <hr className="hairline mt-2 w-full max-w-md" />
      </Reveal>
    </section>
  );
}
