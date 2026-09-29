import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';

import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Accordion } from '@/components/ui/Accordion';
import { Badge } from '@/components/ui/Badge';
import { DataTable } from '@/components/ui/DataTable';
import { Breadcrumb, Pagination } from '@/components/ui/Navigation';
import { Progress } from '@/components/ui/Progress';
import { StateSlot } from '@/components/ui/StateSlot';
import { Tabs } from '@/components/ui/Tabs';

export const dynamic = 'force-static';

export const metadata: Metadata = {
  title: 'Component gallery — Design System',
  description:
    'Every primitive at every density and every required state, rendered from the real code rather than a screenshot.',
  robots: { index: false, follow: false },
};

const DENSITIES = ['cozy', 'compact', 'dense'] as const;

/**
 * A gallery of the real components, at every density and in every state the
 * master plan requires.
 *
 * This exists because the Storybook dependency could not be installed in the
 * environment, and a component library with no browsable catalogue is the thing
 * the wave-4 requirements were written against. It renders the same components
 * the product renders, from the same imports, so a change to a primitive shows
 * up here without anyone maintaining a second copy.
 */
export default async function GalleryPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const labels = {
    loading: t('statusLine.noData'),
    empty: t('market.template.unavailableDescription'),
    error: t('common.error'),
    offline: t('offline.description'),
    partial: t('market.template.unavailableDescription'),
    action: t('common.retry'),
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="display text-3xl font-bold text-ink">{t('brand.name')}</h1>
        <p className="mt-2 text-ink-soft">{t('a11y.skipToContent')}</p>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">Badge — density and tone</h2>
          <div className="mt-3 flex flex-wrap gap-3">
            {(['neutral', 'info', 'success', 'warn', 'bad'] as const).map((tone) => (
              <Badge key={tone} tone={tone} dot>
                {tone}
              </Badge>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            {DENSITIES.map((density) => (
              <Badge key={density} density={density} tone="success">
                {density}
              </Badge>
            ))}
          </div>
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">
            Progress — determinate and indeterminate
          </h2>
          <div className="mt-3 space-y-3">
            <Progress label="cozy" value={42} detail="42 / 100" size="cozy" />
            <Progress label="compact" value={78} size="compact" />
            <Progress label="dense" value={100} size="dense" tone="success" />
            <Progress label="indeterminate" size="cozy" />
          </div>
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">The five required states</h2>
          <p className="mt-1 text-sm text-ink-soft">
            Every data-bearing surface must be able to render all five.
          </p>
          <div className="mt-3 space-y-3">
            {(['ready', 'loading', 'empty', 'error', 'partial', 'offline'] as const).map(
              (state) => (
                <StateSlot key={state} state={state} labels={labels} density="cozy">
                  <p className="text-sm text-ink-soft">{state}</p>
                </StateSlot>
              ),
            )}
          </div>
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">Tabs — roving tabindex</h2>
          <Tabs
            className="mt-3"
            label="gallery"
            items={[
              { id: 'a', label: 'Alpha', hint: '12' },
              { id: 'b', label: 'Beta' },
              { id: 'c', label: 'Gamma', disabled: true },
            ]}
            activeId="a"
            onChange={() => {}}
          />
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">Accordion</h2>
          <Accordion
            className="mt-3"
            label="gallery"
            items={[
              { id: 'one', title: 'First', summary: 'A summary line', content: <p>Body text</p> },
              { id: 'two', title: 'Second', content: <p>More body text</p> },
            ]}
          />
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">Navigation</h2>
          <Breadcrumb
            className="mt-3"
            label="gallery"
            items={[
              { href: `/${locale}`, label: 'root' },
              { href: `/${locale}/a`, label: 'middle' },
              { href: `/${locale}/a/b`, label: 'current' },
            ]}
          />
          <Pagination
            className="mt-4"
            page={1}
            pageCount={5}
            hrefFor={(page) => `/${locale}/page/${page}`}
            label="pagination"
            previousLabel="prev"
            nextLabel="next"
          />
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">DataTable — logical alignment</h2>
          <DataTable
            className="mt-3"
            density="compact"
            caption="Gallery rows"
            rowKey={(row) => String(row.id)}
            columns={[
              { key: 'name', header: 'name', sortable: true },
              { key: 'value', header: 'value', numeric: true, sortable: true },
            ]}
            rows={[
              { id: 1, name: 'alpha', value: 30 },
              { id: 2, name: 'beta', value: 10 },
              { id: 3, name: 'gamma', value: 20 },
            ]}
          />
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-ink">ProvenanceStamp</h2>
          <div className="mt-3 flex flex-wrap gap-4">
            <ProvenanceStamp source="/api/v1/example" label="verified" verified method="GET" />
            <ProvenanceStamp
              source="/api/v1/example"
              label="unverified"
              verified={false}
              method="GET"
            />
          </div>
        </section>
      </div>
    </main>
  );
}
