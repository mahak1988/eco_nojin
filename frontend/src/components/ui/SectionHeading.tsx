import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface SectionHeadingProps {
  kicker: string;
  title: string;
  lead?: string;
  align?: 'start' | 'center';
}

/** Shared section header: small kicker line, big title, optional lead. */
export default function SectionHeading({
  kicker,
  title,
  lead,
  align = 'center',
}: SectionHeadingProps) {
  const { lang } = useLang();
  const alignCls = align === 'center' ? 'items-center text-center' : 'items-start text-start';

  return (
    <Reveal className={`flex flex-col gap-3 ${alignCls}`}>
      <span className="inline-flex items-center gap-2 rounded-full border border-leaf-500/30 bg-leaf-500/10 px-4 py-1 text-xs font-bold tracking-wide text-leaf-300">
        <span className="h-1.5 w-1.5 rounded-full bg-leaf-400 animate-pulse-soft" aria-hidden />
        {kicker}
      </span>
      <h2 className="max-w-2xl text-3xl font-extrabold leading-snug text-emerald-50 sm:text-4xl">
        {title}
      </h2>
      {lead ? (
        <p className={`max-w-2xl text-base leading-8 text-emerald-100/60 ${lang === 'fa' ? 'sm:text-[17px]' : ''}`}>
          {lead}
        </p>
      ) : null}
    </Reveal>
  );
}
