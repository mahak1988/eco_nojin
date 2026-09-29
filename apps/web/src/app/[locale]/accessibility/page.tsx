import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { StateSlot } from '@/components/ui/StateSlot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import {
  CONTRAST_MEASUREMENT,
  EXTERNAL_REVIEW,
  FONT_MEASUREMENT,
  FONT_ROWS,
  INCLUSIVE_CHANNELS,
  type Measurement,
} from './measurements';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.a11y');

  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/accessibility`,
      title: t('metaTitle'),
      description: t('metaDescription'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/accessibility'),
      languages: languageAlternates('/accessibility'),
    },
  };
}

/** The locale-aware number formatter, so a reader reads their own digits. */
function counter(locale: string): (value: number) => string {
  return new Intl.NumberFormat(locale).format;
}

/**
 * One measurement, rendered as a table with the gate that produced it named on
 * the same row. The stamp is `verified={false}` on purpose: the number was
 * produced by a script that ran once, not observed from a live contract, and
 * `verified` means "seen in a live response" everywhere else on this site.
 */
function MeasurementTable({ measurement }: { measurement: Measurement }) {
  return (
    <Card density="compact">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="num font-mono text-xs text-ink-soft">{measurement.script}</p>
        <ProvenanceStamp
          source={measurement.script}
          verified={false}
          method={measurement.measuredAt}
        />
      </div>
      <table className="mt-3 w-full text-sm">
        <caption className="sr-only">{measurement.summary}</caption>
        <tbody>
          {measurement.figures.map((figure) => (
            <tr key={figure.label} className="border-b border-line/50 last:border-b-0">
              <th scope="row" className="num py-2 pe-4 text-start font-mono text-xs text-ink-soft">
                {figure.label}
              </th>
              <td className="num py-2 text-end font-mono text-xs text-ink">{figure.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

export default async function AccessibilityPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.a11y');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const nf = counter(locale);

  /**
   * The inclusive-access claim on this page is the only part of it that can be
   * observed live, so it is the only part that can fail. §4.5 therefore applies
   * to it: the three gateway reads are fetched, and the slot reports what
   * happened to them rather than the page assuming they answered.
   */
  const channels = await Promise.all(
    INCLUSIVE_CHANNELS.map((channel) => apiGet<Record<string, unknown>>(channel.path)),
  );
  const answered = channels.filter((result) => result.ok).length;
  const channelState = (() => {
    if (answered === channels.length) return 'ready' as const;
    if (answered === 0) {
      const offline = channels.every((result) => !result.ok && result.status === 0);
      return offline ? ('offline' as const) : ('error' as const);
    }
    return 'partial' as const;
  })();

  const contrastPairs = CONTRAST_MEASUREMENT.figures[0];
  const bundledRows = FONT_ROWS.filter((row) => row.shipped);
  const fallbackRows = FONT_ROWS.filter((row) => !row.shipped);
  /** Reads a figure out of the record rather than restating it in JSX. */
  const fontFigure = (label: string): number =>
    Number(FONT_MEASUREMENT.figures.find((figure) => figure.label === label)?.value ?? 0);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-16 pt-8">
        <header>
          <h1 className="display text-balance text-4xl font-bold text-ink">{t('metaTitle')}</h1>
          <p className="mt-3 max-w-2xl text-ink-soft">{t('metaDescription')}</p>
        </header>

        <section className="mt-8" aria-labelledby="a11y-measured">
          <h2 id="a11y-measured" className="field-label">
            {t('measuredTitle')}
          </h2>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <section className="card p-5">
              <h3 className="field-label">{t('contrastTitle')}</h3>
              <p className="mt-2 text-sm text-ink-soft">{t('contrastBody')}</p>
              <dl className="mt-4 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <div>
                  <dt className="text-xs text-ink-soft">{t('contrastPairs')}</dt>
                  <dd className="num text-3xl font-semibold text-ink">
                    {nf(Number(contrastPairs.value))}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-soft">{t('contrastFloor')}</dt>
                  <dd className="num text-sm text-ink">
                    {CONTRAST_MEASUREMENT.figures
                      .slice(1)
                      .map((figure) => figure.value)
                      .join(' / ')}
                  </dd>
                </div>
                <div className="ms-auto">
                  <StatusDot state="ok" label={t('contrastPass')} />
                </div>
              </dl>
              <div className="mt-4">
                <MeasurementTable measurement={CONTRAST_MEASUREMENT} />
              </div>
            </section>

            <section className="card p-5">
              <h3 className="field-label">{t('fontsTitle')}</h3>
              <p className="mt-2 text-sm text-ink-soft">{t('fontsBody')}</p>
              <dl className="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-1">
                <div>
                  <dt className="text-xs text-ink-soft">{t('fontsFamilies')}</dt>
                  <dd className="num text-3xl font-semibold text-ink">
                    {nf(fontFigure('families'))}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-soft">{t('fontsFiles')}</dt>
                  <dd className="num text-3xl font-semibold text-ink">{nf(fontFigure('files'))}</dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-soft">{t('fontsLocales')}</dt>
                  <dd className="num text-3xl font-semibold text-ink">
                    {nf(bundledRows.length)}/{nf(FONT_ROWS.length)}
                  </dd>
                </div>
              </dl>
              <div className="mt-4">
                <MeasurementTable measurement={FONT_MEASUREMENT} />
              </div>
            </section>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">{t('fontsBody')}</caption>
              <thead>
                <tr className="border-b border-line text-ink-soft">
                  <th scope="col" className="py-2 pe-4 text-start font-medium">
                    locale
                  </th>
                  <th scope="col" className="py-2 pe-4 text-start font-medium">
                    family
                  </th>
                  <th scope="col" className="py-2 pe-4 text-end font-medium">
                    faces
                  </th>
                  <th scope="col" className="py-2 pe-4 text-end font-medium">
                    bytes
                  </th>
                  <th scope="col" className="py-2 text-start font-medium">
                    {t('fontsBundled')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {FONT_ROWS.map((row) => (
                  <tr key={row.locale} className="border-b border-line/50 align-top">
                    <td className="num py-2 pe-4 font-mono text-xs text-ink">{row.locale}</td>
                    <td className="py-2 pe-4 text-xs text-ink">
                      {row.family}
                      <span className="ms-2 text-ink-faint">{row.script}</span>
                    </td>
                    <td className="num py-2 pe-4 text-end font-mono text-xs text-ink-soft">
                      {nf(row.faces)}
                    </td>
                    <td className="num py-2 pe-4 text-end font-mono text-xs text-ink-soft">
                      {nf(row.bytes)}
                    </td>
                    <td className="py-2 text-xs">
                      <StatusDot
                        state={row.shipped ? 'ok' : 'warn'}
                        label={row.shipped ? t('fontsBundled') : t('fontsFallback')}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="field-label">{t('fontsBundled')}</h3>
                <StatusDot
                  state={bundledRows.length > 0 ? 'ok' : 'down'}
                  label={`${bundledRows.length}/${FONT_ROWS.length}`}
                />
              </div>
            </Card>
            <Card density="compact">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="field-label">{t('fontsFallback')}</h3>
                <StatusDot
                  state={fallbackRows.length > 0 ? 'warn' : 'ok'}
                  label={nf(fallbackRows.length)}
                />
              </div>
              <p className="mt-2 text-sm text-ink-soft">{t('fontsGap')}</p>
            </Card>
          </div>
        </section>

        <section className="mt-8 grid gap-4 sm:grid-cols-2" aria-labelledby="a11y-practice">
          <h2 id="a11y-practice" className="sr-only">
            {t('measuredTitle')}
          </h2>
          <div className="card p-5">
            <h3 className="field-label">{t('assistiveTitle')}</h3>
            <p className="mt-2 text-sm text-ink-soft">{t('assistiveBody')}</p>
          </div>
          <div className="card p-5">
            <h3 className="field-label">{t('inclusiveTitle')}</h3>
            <p className="mt-2 text-sm text-ink-soft">{t('inclusiveBody')}</p>
          </div>
        </section>

        <section className="mt-8" aria-labelledby="a11y-channels">
          <h2 id="a11y-channels" className="field-label">
            {t('inclusiveTitle')}
          </h2>
          <div className="mt-3">
            <StateSlot
              state={channelState}
              density="compact"
              labels={{
                loading: common('retry'),
                empty: statusLine('noData'),
                error: statusLine('unavailable'),
                partial: statusLine('realData'),
                offline: statusLine('unavailable'),
              }}
              detail={`${answered}/${INCLUSIVE_CHANNELS.length} · ${INCLUSIVE_CHANNELS.map(
                (channel) => channel.path,
              ).join(' · ')}`}
            >
              <ul className="grid gap-3">
                {INCLUSIVE_CHANNELS.map((channel, index) => {
                  const result = channels[index];
                  return (
                    <li
                      key={channel.id}
                      className="card flex flex-wrap items-center justify-between gap-3 p-4"
                    >
                      <span className="num font-mono text-xs text-ink">{channel.path}</span>
                      <span className="flex items-center gap-3">
                        <span className="num text-xs text-ink-soft">
                          {result.ok ? statusLine('realData') : statusLine('unavailable')}
                        </span>
                        <StatusDot
                          state={result.ok ? 'ok' : 'down'}
                          label={result.ok ? common('live') : statusLine('unavailable')}
                        />
                      </span>
                    </li>
                  );
                })}
              </ul>
            </StateSlot>
          </div>
        </section>

        <div className="mt-8 grid gap-4">
          <ListBlock
            title={t('notClaimedTitle')}
            items={t.raw('notClaimedItems') as string[]}
            tone="clay"
          />
          <section className="card p-5">
            <h2 className="field-label">{t('feedbackTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{t('feedbackBody')}</p>
            <p className="num mt-3 text-xs text-ink-faint">
              {t('measuredAt')}: {CONTRAST_MEASUREMENT.measuredAt} · {CONTRAST_MEASUREMENT.command}{' '}
              · {FONT_MEASUREMENT.command}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <ProvenanceStamp source={CONTRAST_MEASUREMENT.script} verified={false} />
              <ProvenanceStamp source={FONT_MEASUREMENT.script} verified={false} />
            </div>
            <p className="num mt-3 text-xs text-ink-faint">
              audit={String(EXTERNAL_REVIEW.audit)} · study=
              {String(EXTERNAL_REVIEW.assistiveTechnologyStudy)} · screenReader=
              {String(EXTERNAL_REVIEW.screenReaderAutomation)} · level=
              {EXTERNAL_REVIEW.conformanceLevel ?? '—'}
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
