import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { StateSlot } from '@/components/ui/StateSlot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';

const LIST_PATH = '/api/v1/legal-texts';
const LOCALES_PATH = '/api/v1/legal-texts/locales';
const SLUGS_PATH = '/api/v1/legal-texts/slugs';
const VERSIONS_SUFFIX = '/versions';

type LegalText = {
  id: string;
  locale: string;
  slug: string;
  title: string;
  body: string;
  version: number;
  status: string;
  effective_at: string | null;
  updated_at: string | null;
};

type Registry = { count: number; legal_texts: LegalText[] };

type LegalTextVersion = {
  version: number;
  status: string;
  effective_at: string | null;
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.legalTexts');

  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/legal`,
      title: t('metaTitle'),
      description: t('metaDescription'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/legal'),
      languages: languageAlternates('/legal'),
    },
  };
}

export default async function LegalPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.legalTexts');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const market = await getTranslations('market.template');
  const nf = new Intl.NumberFormat(locale);

  /**
   * Four published reads, all of which exist: the registry, the two bare arrays
   * and the version history of the newest text in this locale.
   *
   * The last one is a dependent request — it needs a slug, and the slug comes
   * back from the registry. Guessing a slug would put a 404 on the page, so the
   * request is issued only once the registry has answered.
   */
  const registry = await apiGet<Registry>(LIST_PATH);
  const all = registry.ok ? registry.data.legal_texts : [];
  const published = all.filter((text) => text.locale === locale && text.status === 'published');
  const latest = published.sort((a, b) => b.version - a.version)[0] ?? null;

  const [locales, slugs, versions] = await Promise.all([
    apiGet<string[]>(LOCALES_PATH),
    apiGet<string[]>(SLUGS_PATH),
    latest
      ? apiGet<LegalTextVersion[]>(`${LIST_PATH}/${latest.locale}/${latest.slug}${VERSIONS_SUFFIX}`)
      : Promise.resolve({ ok: false as const, status: 0, error: 'no published slug' }),
  ]);

  const answered = [registry, locales, slugs].filter((result) => result.ok).length;
  const state = (() => {
    if (answered === 3) return 'ready' as const;
    if (answered === 0) {
      return [registry, locales, slugs].every((result) => !result.ok && result.status === 0)
        ? ('offline' as const)
        : ('error' as const);
    }
    return 'partial' as const;
  })();

  const localeRows = locales.ok ? locales.data : [];
  const slugRows = slugs.ok ? slugs.data : [];
  const versionRows = versions.ok ? versions.data : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <article className="mx-auto max-w-3xl px-6 pb-16 pt-8">
        <header>
          <h1 className="display text-3xl font-bold text-balance text-ink sm:text-4xl">
            {t('metaTitle')}
          </h1>
          <p className="mt-3 text-sm text-ink-soft">{t('metaDescription')}</p>
        </header>

        <section className="mt-6" aria-labelledby="legal-state">
          <h2 id="legal-state" className="field-label">
            {t('metaTitle')}
          </h2>
          <div className="mt-3">
            <StateSlot
              state={state}
              density="compact"
              labels={{
                loading: common('retry'),
                empty: statusLine('noData'),
                error: statusLine('unavailable'),
                partial: market('unavailableTitle'),
                offline: statusLine('unavailable'),
              }}
              detail={`${answered}/3 · ${LIST_PATH} · ${LOCALES_PATH} · ${SLUGS_PATH}`}
            >
              <ul className="grid gap-2">
                {[
                  {
                    path: LIST_PATH,
                    ok: registry.ok,
                    detail: registry.ok ? nf.format(registry.data.count) : null,
                  },
                  {
                    path: LOCALES_PATH,
                    ok: locales.ok,
                    detail: locales.ok ? nf.format(localeRows.length) : null,
                  },
                  {
                    path: SLUGS_PATH,
                    ok: slugs.ok,
                    detail: slugs.ok ? nf.format(slugRows.length) : null,
                  },
                ].map((row) => (
                  <li
                    key={row.path}
                    className="card flex flex-wrap items-center justify-between gap-3 p-4"
                  >
                    <span className="num font-mono text-xs text-ink">{row.path}</span>
                    <span className="flex items-center gap-3">
                      <span className="num text-xs text-ink-soft">
                        {row.ok
                          ? (row.detail ?? statusLine('realData'))
                          : statusLine('unavailable')}
                      </span>
                      <ProvenanceStamp source={row.path} verified={row.ok} />
                      <StatusDot
                        state={row.ok ? 'ok' : 'down'}
                        label={row.ok ? common('live') : statusLine('unavailable')}
                      />
                    </span>
                  </li>
                ))}
              </ul>
            </StateSlot>
          </div>
        </section>

        <section className="mt-8" aria-labelledby="legal-documents">
          <h2 id="legal-documents" className="field-label">
            {t('metaTitle')}
          </h2>
          {published.length > 0 ? (
            <div className="mt-3 grid gap-4">
              {published.map((text) => (
                <Card density="cozy" key={text.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <h3 className="text-lg font-semibold text-ink">{text.title}</h3>
                    <ProvenanceStamp
                      source={`${LIST_PATH}/${text.locale}/${text.slug}`}
                      verified
                      timestamp={text.updated_at ?? undefined}
                    />
                  </div>
                  <dl className="mt-3 grid gap-3 sm:grid-cols-3">
                    <div>
                      <dt className="field-label">{t('versionLabel')}</dt>
                      <dd className="num mt-1 font-mono text-sm text-ink">
                        {nf.format(text.version)}
                      </dd>
                    </div>
                    <div>
                      <dt className="field-label">{t('statusLabel')}</dt>
                      <dd className="num mt-1 font-mono text-sm text-ink">{text.status}</dd>
                    </div>
                    <div>
                      <dt className="field-label">{t('effectiveLabel')}</dt>
                      <dd className="num mt-1 font-mono text-sm text-ink">
                        {text.effective_at ?? '—'}
                      </dd>
                    </div>
                  </dl>
                  <p className="mt-4 text-sm whitespace-pre-wrap text-ink-soft">{text.body}</p>
                </Card>
              ))}
            </div>
          ) : (
            <Card density="cozy" className="mt-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-sm font-medium text-ink">{t('publishedOnly')}</h3>
                <StatusDot
                  state={registry.ok ? 'warn' : 'down'}
                  label={statusLine('unavailable')}
                />
              </div>
              <p className="num mt-3 text-xs text-ink-soft">
                {LIST_PATH}?locale={locale}&status=published ·{' '}
                {registry.ok ? nf.format(registry.data.count) : statusLine('unavailable')}
              </p>
            </Card>
          )}
        </section>

        <section className="mt-8" aria-labelledby="legal-versions">
          <h2 id="legal-versions" className="field-label">
            {t('versionsTitle')}
          </h2>
          <div className="mt-3">
            <StateSlot
              state={versions.ok ? 'ready' : 'empty'}
              density="compact"
              labels={{
                loading: common('retry'),
                empty: t('publishedOnly'),
                error: statusLine('unavailable'),
                partial: statusLine('realData'),
                offline: statusLine('unavailable'),
              }}
              detail={
                latest
                  ? `${LIST_PATH}/${latest.locale}/${latest.slug}${VERSIONS_SUFFIX}`
                  : VERSIONS_SUFFIX
              }
            >
              <Card density="compact">
                <table className="w-full text-sm">
                  <caption className="sr-only">{t('versionsTitle')}</caption>
                  <thead>
                    <tr className="border-b border-line text-ink-soft">
                      <th scope="col" className="num py-2 pe-4 text-start font-medium">
                        {t('versionLabel')}
                      </th>
                      <th scope="col" className="num py-2 pe-4 text-start font-medium">
                        {t('statusLabel')}
                      </th>
                      <th scope="col" className="num py-2 text-start font-medium">
                        {t('effectiveLabel')}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {versionRows.map((item) => (
                      <tr key={item.version} className="border-b border-line/50">
                        <td className="num py-2 pe-4 font-mono text-ink">
                          {nf.format(item.version)}
                        </td>
                        <td className="num py-2 pe-4 font-mono text-ink-soft">{item.status}</td>
                        <td className="num py-2 font-mono text-ink-soft">
                          {item.effective_at ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            </StateSlot>
          </div>
        </section>

        <section className="mt-8 grid gap-4 sm:grid-cols-2">
          <Card density="compact">
            <h3 className="field-label">{t('localesTitle')}</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {localeRows.length > 0 ? (
                localeRows.map((entry) => (
                  <span
                    key={entry}
                    className="num rounded bg-forest/10 px-2 py-1 text-xs text-forest"
                  >
                    {entry}
                  </span>
                ))
              ) : (
                <p className="text-sm text-ink-soft">{statusLine('noData')}</p>
              )}
            </div>
          </Card>
          <Card density="compact">
            <h3 className="field-label">{t('slugsTitle')}</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {slugRows.length > 0 ? (
                slugRows.map((slug) => (
                  <span
                    key={slug}
                    className="num rounded bg-forest/10 px-2 py-1 text-xs text-forest"
                  >
                    {slug}
                  </span>
                ))
              ) : (
                <p className="text-sm text-ink-soft">{statusLine('noData')}</p>
              )}
            </div>
          </Card>
        </section>
      </article>
    </main>
  );
}
