import { getTranslations } from 'next-intl/server';

type FivePartProps = {
  title: string;
  lead: string;
  what: string;
  audience: string;
  evidence: string[];
  limits: string[];
  next: string[];
  evidenceLabel?: string;
  limitsLabel?: string;
  nextLabel?: string;
};

/**
 * T02 template — «چه/برای چه‌کسی/شواهد/محدودیت/گام بعدی»
 * The fixed five-part structure required for every public page
 * (master plan §۶.۱). Limits are always rendered prominently.
 */
export async function FivePart({
  title,
  lead,
  what,
  audience,
  evidence,
  limits,
  next,
  evidenceLabel,
  limitsLabel,
  nextLabel,
}: FivePartProps) {
  const t = await getTranslations();
  return (
    <div className="space-y-8">
      <header>
        <h1 className="display text-balance text-4xl font-bold text-ink sm:text-5xl">{title}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{lead}</p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="card p-5" aria-labelledby="fp-what">
          <h2 id="fp-what" className="field-label">
            {t('common.whatLabel')}
          </h2>
          <p className="mt-2 text-sm text-ink">{what}</p>
        </section>
        <section className="card p-5" aria-labelledby="fp-audience">
          <h2 id="fp-audience" className="field-label">
            {t('common.audienceLabel')}
          </h2>
          <p className="mt-2 text-sm text-ink">{audience}</p>
        </section>
      </div>

      {evidence.length > 0 ? (
        <section aria-labelledby="fp-evidence">
          <h2 id="fp-evidence" className="field-label">
            {evidenceLabel ?? t('common.evidenceLabel')}
          </h2>
          <ul className="mt-3 space-y-2">
            {evidence.map((item, index) => (
              <li key={item} className="card flex items-baseline gap-3 px-4 py-3 text-sm text-ink">
                <span className="num text-xs text-ink-faint">{index + 1}</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {limits.length > 0 ? (
        <section
          aria-labelledby="fp-limits"
          className="card border-clay/40 p-5"
          style={{ borderColor: 'color-mix(in oklch, var(--clay) 40%, var(--line))' }}
        >
          <h2 id="fp-limits" className="field-label text-clay">
            {limitsLabel ?? t('common.limitsLabel')}
          </h2>
          <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-ink">
            {limits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {next.length > 0 ? (
        <section aria-labelledby="fp-next">
          <h2 id="fp-next" className="field-label text-moss">
            {nextLabel ?? t('common.nextLabel')}
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-ink">
            {next.map((item) => (
              <li key={item} className="flex items-baseline gap-2">
                <span aria-hidden="true" className="text-moss">
                  ↳
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
