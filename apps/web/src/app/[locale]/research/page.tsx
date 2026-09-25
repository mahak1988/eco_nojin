import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import {
  CONTRACT_DETAIL_LABEL_KEY,
  CONTRACT_LABEL_KEY,
  EMPTY_DETAIL_LABEL_KEY,
  EMPTY_TITLE_LABEL_KEY,
  isCapabilityWired,
  NEXT_DETAIL_KEY,
  NEXT_LABEL_KEY,
  REAL_DATA_LABEL_KEY,
  RESEARCH_WORKSPACE_ROUTE,
  SERVICE_LABEL_KEY,
  STATE_LABEL_KEY,
  UNAVAILABLE_DETAIL_KEY,
  UNAVAILABLE_LABEL_KEY,
  UNAVAILABLE_TITLE_KEY,
} from '@/lib/domains/registry';

// Datasets, experiments and citations are re-resolved on every request.
export const dynamic = 'force-dynamic';

export default async function ResearchPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <div>
      <header>
        <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
          {t(RESEARCH_WORKSPACE_ROUTE.headingKey)}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-soft">{t('evidence.lead')}</p>
      </header>

      <section className="card mt-6 p-5" aria-labelledby="research-state">
        <h2 id="research-state" className="field-label">
          {t(STATE_LABEL_KEY)}
        </h2>
        <p className="mt-3 text-sm text-ink">{t(UNAVAILABLE_TITLE_KEY)}</p>
        <p className="mt-2 text-sm text-ink-soft">{t(UNAVAILABLE_DETAIL_KEY)}</p>
      </section>

      <section className="mt-4" aria-labelledby="research-capabilities">
        <h2 id="research-capabilities" className="field-label">
          {t(CONTRACT_LABEL_KEY)}
        </h2>
        <ul className="mt-3 space-y-2">
          {RESEARCH_WORKSPACE_ROUTE.capabilities.map((capability) => (
            <li
              key={capability.id}
              className="card flex flex-wrap items-center justify-between gap-3 p-4"
            >
              <span className="text-sm text-ink">{t(capability.labelKey)}</span>
              <span className="flex flex-wrap items-center gap-3">
                <span className="num text-xs text-ink-faint">
                  {capability.endpoint ?? t(UNAVAILABLE_LABEL_KEY)}
                </span>
                <StatusDot
                  state={isCapabilityWired(capability) ? 'warn' : 'down'}
                  label={
                    isCapabilityWired(capability) ? t('common.planned') : t(UNAVAILABLE_LABEL_KEY)
                  }
                />
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="card mt-4 p-5" aria-labelledby="research-records">
        <h2 id="research-records" className="field-label">
          {t(EMPTY_TITLE_LABEL_KEY)}
        </h2>
        <p className="mt-2 text-sm text-ink-soft">{t(EMPTY_DETAIL_LABEL_KEY)}</p>
      </section>

      <section className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="card p-5">
          <h2 className="field-label">{t(SERVICE_LABEL_KEY)}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t(CONTRACT_DETAIL_LABEL_KEY)}</p>
        </div>
        <div className="card p-5">
          <h2 className="field-label">{t(NEXT_LABEL_KEY)}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t(NEXT_DETAIL_KEY)}</p>
        </div>
      </section>

      <p className="mt-6 text-xs text-ink-soft">{t(REAL_DATA_LABEL_KEY)}</p>
    </div>
  );
}
