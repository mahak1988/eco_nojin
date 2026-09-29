import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ListBlock } from '@/components/ListBlock';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';

const VALIDATION_PATH = '/api/v1/hydroma/validation';

type ValidationCheck = {
  id: string;
  label: string;
  kind: string;
  source: string;
  expected: number | null;
  actual: number | null;
  tolerance: number | null;
  unit: string | null;
  passed: boolean;
  note: string;
};

type ValidationReport = {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  checks: ValidationCheck[];
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('evidence');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/validation`,
      title: t('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/validation'),
      languages: languageAlternates('/validation'),
    },
  };
}

export default async function ValidationPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const nf = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

  const report = await apiGet<ValidationReport>(VALIDATION_PATH);
  const data = report.ok ? report.data : null;
  const checks = data?.checks ?? [];
  const state: DotState = !data ? 'down' : data.failed === 0 ? 'ok' : 'warn';

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <FivePart
          title={t('evidence.title')}
          lead={t('evidence.lead')}
          what={t('evidence.what')}
          audience={t('evidence.audience')}
          evidence={t.raw('evidence.evidence') as string[]}
          limits={t.raw('evidence.limits') as string[]}
          next={t.raw('evidence.next') as string[]}
        />

        <section className="mt-10" aria-labelledby="validation-report">
          <h2 id="validation-report" className="field-label">
            {statusPage('rows')}
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <span className="chip num font-mono">{VALIDATION_PATH}</span>
            <StatusDot
              state={state}
              label={state === 'down' ? statusLine('unavailable') : statusLine('realData')}
            />
            {data && (
              <span className="num text-xs text-ink-soft">
                {common('total')}: {nf.format(data.total)} · {statusPage('result')}:{' '}
                {nf.format(data.passed)}/{nf.format(data.total)}
              </span>
            )}
          </div>

          {checks.length === 0 ? (
            <p className="mt-4 text-sm text-ink-soft">
              {report.ok ? statusLine('noData') : statusLine('unavailable')}
            </p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-ink-soft">
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('label')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('result')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('state')}</th>
                    <th className="py-2 text-start font-medium">{statusPage('service')}</th>
                  </tr>
                </thead>
                <tbody>
                  {checks.map((check) => (
                    <tr key={check.id} className="border-b border-line/50 align-top">
                      <td className="py-2 pe-4">
                        <span className="font-mono text-xs text-ink">{check.id}</span>
                        <p className="mt-1 text-xs text-ink-soft">{check.label}</p>
                      </td>
                      <td className="num py-2 pe-4 text-ink-soft">
                        {check.expected === null ? '—' : nf.format(check.expected)}
                        {check.tolerance !== null ? ` ± ${nf.format(check.tolerance)}` : ''}
                        {check.unit ? ` ${check.unit}` : ''}
                        {check.actual === null ? '' : ` → ${nf.format(check.actual)}`}
                      </td>
                      <td
                        className={`py-2 pe-4 text-xs ${check.passed ? 'text-forest' : 'text-copper'}`}
                      >
                        {check.passed ? common('live') : statusLine('unavailable')}
                      </td>
                      <td className="py-2 text-xs text-ink-soft">
                        {check.kind}
                        {check.source ? ` · ${check.source}` : ''}
                        {check.note ? ` · ${check.note}` : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={common('limitsLabel')}
            items={t.raw('evidence.limits') as string[]}
            tone="clay"
          />
          <ListBlock
            title={common('nextLabel')}
            items={t.raw('evidence.next') as string[]}
            tone="moss"
          />
        </div>
      </div>
    </main>
  );
}
