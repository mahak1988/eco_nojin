import { getTranslations, setRequestLocale } from 'next-intl/server';
import { EmptyState } from '@/components/EmptyState';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { apiGet } from '@/lib/api/client';

export const dynamic = 'force-dynamic';

type LegalText = {
  id: string;
  locale: string;
  slug: string;
  title: string;
  body: string;
  version: number;
  status: string;
  effective_at: string | null;
};

const LIST_PATH = '/api/v1/legal-texts';

export default async function LegalPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const nf = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

  const registry = await apiGet<{ count: number; legal_texts: LegalText[] }>(LIST_PATH);

  const texts = registry.ok
    ? registry.data.legal_texts.filter(
        (text) => text.locale === locale && text.status === 'published',
      )
    : [];
  const state: DotState = !registry.ok ? 'down' : texts.length > 0 ? 'ok' : 'warn';

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <article className="mx-auto max-w-3xl px-6 py-10">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="display text-4xl font-bold text-ink">{t('legal.title')}</h1>
          <span className="chip num">{t('legal.version')}</span>
        </header>
        <p className="mt-3 text-ink-soft">{t('legal.lead')}</p>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <span className="chip num font-mono">{LIST_PATH}</span>
          <StatusDot
            state={state}
            label={state === 'down' ? statusLine('unavailable') : statusLine('realData')}
          />
          <span className="num text-xs text-ink-soft">
            {statusPage('rows')}: {texts.length}
          </span>
        </div>

        {texts.length > 0 ? (
          <div className="mt-6 grid gap-4">
            {texts.map((text) => (
              <section key={text.id} className="card p-6">
                <h2 className="field-label">{text.title}</h2>
                <p className="num mt-2 text-xs text-ink-soft">
                  {text.slug} · {text.locale} · {nf.format(text.version)}
                  {text.effective_at ? ` · ${text.effective_at.slice(0, 10)}` : ''}
                </p>
                <p className="mt-3 whitespace-pre-wrap text-sm text-ink">{text.body}</p>
              </section>
            ))}
          </div>
        ) : (
          <div className="mt-8">
            <EmptyState message={t('learn.emptyTitle')} detail={t('learn.emptyDesc')} />
          </div>
        )}
      </article>
    </main>
  );
}
