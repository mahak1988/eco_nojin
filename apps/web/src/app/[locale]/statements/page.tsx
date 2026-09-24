import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

/** T09 — document template: versioned, dated, print-clean. */
export default async function StatementsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <article className="mx-auto max-w-3xl px-6 py-10">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="display text-balance text-4xl font-bold text-ink">
            {t('statements.title')}
          </h1>
          <span className="chip num">{t('statements.versionLabel')}</span>
        </header>
        <p className="mt-3 text-ink-soft">{t('statements.lead')}</p>

        <section className="card mt-8 p-6">
          <h2 className="field-label">{t('statements.missionTitle')}</h2>
          <p className="mt-3 leading-relaxed text-ink">{t('statements.missionBody')}</p>
        </section>

        <blockquote className="mt-8 border-s-2 border-water/60 ps-4">
          <p className="text-sm text-ink-soft">{t('cover.quote')}</p>
          <footer className="chip mt-3">{t('statements.quoteLabel')}</footer>
        </blockquote>

        <section className="card mt-8 p-6">
          <h2 className="field-label">{t('statements.transparencyTitle')}</h2>
          <p className="mt-3 text-sm text-ink">{t('statements.transparencyBody')}</p>
        </section>
      </article>
    </main>
  );
}
