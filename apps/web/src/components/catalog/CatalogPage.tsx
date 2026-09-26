import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { type CatalogEntry, getCatalogGroup } from '@/lib/domains/page-catalog';

/** The gate document every catalog surface has to pass before it ships. */
const PAGE_GATES_DOC = 'docs/frontend/PAGE_GATES.md';

const DOT_STATE: Record<CatalogEntry['status'], DotState> = {
  live: 'ok',
  capability: 'ok',
  planned: 'warn',
  unavailable: 'down',
};

const STATUS_LABEL_KEY = {
  live: 'common.live',
  capability: 'common.beta',
  planned: 'common.planned',
  unavailable: 'statusLine.unavailable',
} as const satisfies Record<CatalogEntry['status'], string>;

interface CatalogPageProps {
  locale: string;
  entry: CatalogEntry;
}

/**
 * Fallback page for a catalog surface that has no page of its own.
 *
 * It reports the registry record and nothing else: no sample value, no success
 * state and no `verified` provenance claim. `ProvenanceStamp` is always rendered
 * with `verified={false}`, because a registry entry is a declaration of intent,
 * not an observation of data.
 */
export async function CatalogPage({ locale, entry }: CatalogPageProps) {
  setRequestLocale(locale);
  const t = await getTranslations();
  const group = getCatalogGroup(entry.domain);
  const statusLabel = t(STATUS_LABEL_KEY[entry.status]);
  const landingHref = group ? `/${locale}${group.landing}` : `/${locale}`;
  const endpointLabel = entry.endpoint ?? t('statusLine.unavailable');

  return (
    <main id="main-content" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <Link href={landingHref} className="text-sm text-[var(--color-forest)]">
          {t('common.back')}
          <span className="num ms-2 font-mono text-xs">{group?.landing ?? ''}</span>
        </Link>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <StatusDot state={DOT_STATE[entry.status]} label={statusLabel} />
          <span className="num font-mono text-xs text-ink-soft">{entry.path}</span>
          <ProvenanceStamp
            source={entry.sourceOfTruth}
            label={t('market.template.source')}
            verified={false}
            method={entry.method}
            labels={{
              heading: t('auth.common.provenance.heading'),
              source: t('auth.common.provenance.source'),
              method: t('auth.common.provenance.method'),
              verified: t('auth.common.provenance.verified'),
              unverified: t('auth.common.provenance.unverified'),
            }}
          />
        </div>

        <Card density="cozy" className="mt-6">
          <h1 className="display text-3xl font-bold text-ink">
            {t('market.template.unavailableTitle')}
          </h1>
          <p className="mt-3 text-ink-soft">{t('market.template.unavailableDescription')}</p>
          <p className="mt-4 text-sm text-ink-soft">{entry.description}</p>

          <dl className="mt-6 grid gap-3 rounded-md border border-line p-4 sm:grid-cols-2">
            <div>
              <dt className="field-label">{t('statusPage.state')}</dt>
              <dd className="mt-1 text-sm text-ink">{statusLabel}</dd>
            </div>
            <div>
              <dt className="field-label">{t('statusPage.endpoint')}</dt>
              <dd className="num mt-1 break-all text-sm text-ink">{endpointLabel}</dd>
            </div>
            <div>
              <dt className="field-label">{t('market.template.source')}</dt>
              <dd className="num mt-1 break-all text-sm text-ink">{entry.sourceOfTruth}</dd>
            </div>
            <div>
              <dt className="field-label">{t('market.template.method')}</dt>
              <dd className="num mt-1 text-sm text-ink">{entry.method}</dd>
            </div>
          </dl>

          <div className="mt-6 rounded-md border border-line p-4">
            <h2 className="font-semibold text-ink">{t('market.template.contractTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{t('market.template.contractDescription')}</p>
            <p className="num mt-3 break-all text-xs text-ink-faint">
              {entry.owner} · {entry.gate} · {entry.access}
            </p>
            <p className="mt-3">
              <ProvenanceStamp
                source={PAGE_GATES_DOC}
                label={t('market.template.contractTitle')}
                verified={false}
                labels={{
                  heading: t('auth.common.provenance.heading'),
                  source: t('auth.common.provenance.source'),
                  unverified: t('auth.common.provenance.unverified'),
                }}
              />
            </p>
          </div>

          <div className="mt-6 rounded-md border border-line p-4">
            <h2 className="font-semibold text-ink">{t('market.template.nextTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{t('market.template.nextDescription')}</p>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-4">
            <Link href={`/${locale}/status`} className="text-sm text-[var(--color-forest)]">
              {t('statusPage.title')}
              <span className="ms-2 text-xs text-ink-soft">{t('statusPage.subtitle')}</span>
            </Link>
          </div>
        </Card>
      </div>
    </main>
  );
}
