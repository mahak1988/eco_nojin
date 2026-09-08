import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface PageHeaderProps {
  kicker: string;
  title: string;
  lead: string;
}

/** Shared top block for inner pages. */
export default function PageHeader({ kicker, title, lead }: PageHeaderProps) {
  const { lang } = useLang();

  return (
    <section className="px-4 pb-8 pt-14 sm:px-6 lg:pt-20">
      <Reveal className="mx-auto flex max-w-6xl flex-col items-start gap-4">
        <span className="inline-flex items-center gap-2 rounded-full border border-leaf-500/30 bg-leaf-500/10 px-4 py-1 text-xs font-bold text-leaf-300">
          <span className="h-1.5 w-1.5 rounded-full bg-leaf-400 animate-pulse-soft" aria-hidden />
          {kicker}
        </span>
        <h1 className="max-w-3xl text-3xl font-extrabold leading-snug text-emerald-50 sm:text-5xl sm:leading-tight">
          {title}
        </h1>
        <p
          className={`max-w-2xl text-base leading-8 text-emerald-100/60 ${
            lang === 'fa' ? 'sm:text-lg sm:leading-9' : ''
          }`}
        >
          {lead}
        </p>
      </Reveal>
    </section>
  );
}
