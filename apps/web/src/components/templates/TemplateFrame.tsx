import type { ReactNode } from 'react';

import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Badge } from '@/components/ui/Badge';
import { type DataState, StateSlot } from '@/components/ui/StateSlot';
import {
  type PageDensity,
  type PageTemplate,
  type RequiredRegion,
  renderTemplateChildren,
  type TemplateChildren,
  type TemplateLabels,
} from '@/lib/design/page-templates';

/**
 * The chrome every one of the twelve templates shares, and nothing more.
 *
 * The plan's gap table records that 110 scientific pages render on one
 * archetype. The cure is not twelve hand-written shells — it is one shell that
 * cannot be got wrong, plus twelve layouts that differ in what a reader can do.
 * So the four things the plan makes non-negotiable live here and nowhere else:
 *
 *   - the five states of §4.5, through `StateSlot`, which already speaks
 *     `loading | empty | error | partial | offline | ready`;
 *   - the source stamp, which is *placed* rather than left to the caller: it is
 *     rendered inside the region named by `template.provenance.anchor`, so the
 *     stamp sits on the numeric region by construction;
 *   - `provenance`, `state` and `data`, which no template can leave out of its
 *     declared region order and still type-check;
 *   - heading order: one `<h1>`, then one `<h2>` per labelled region.
 *
 * The templates pass their own extra regions and their own layout. Nothing here
 * is a client component; `StateSlot` and `Card` are, and the island stops there.
 */

/** How a template arranges its regions. This is the layout signature. */
export type TemplateLayout =
  /** Full-bleed, uncapped width. The cover. */
  | 'hero'
  /** One centred reading column. */
  | 'column'
  /** Wide single column, for a dense surface. */
  | 'wide'
  /** Main column with a sticky action/summary rail at the inline end. */
  | 'split'
  /** Two equal panels, side by side. */
  | 'panels';

const DENSITY_GAP: Record<PageDensity, string> = {
  comfortable: 'gap-6',
  compact: 'gap-4',
  dense: 'gap-2',
};

/**
 * `StateSlot` speaks `cozy | compact | dense`; the plan speaks
 * `comfortable | compact | dense`. Naming the plan's word in the design layer
 * and translating here keeps one vocabulary per layer.
 */
const SLOT_DENSITY: Record<PageDensity, 'cozy' | 'compact' | 'dense'> = {
  comfortable: 'cozy',
  compact: 'compact',
  dense: 'dense',
};

const LAYOUT_SHELL: Record<TemplateLayout, string> = {
  hero: 'mx-auto flex w-full max-w-none flex-col px-4 pb-16 sm:px-6',
  column: 'mx-auto flex w-full max-w-3xl flex-col px-4 pb-16 sm:px-6',
  wide: 'mx-auto flex w-full max-w-7xl flex-col px-4 pb-16 sm:px-6',
  split:
    'mx-auto grid w-full max-w-7xl grid-cols-1 items-start gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[minmax(0,1fr)_20rem]',
  panels:
    'mx-auto grid w-full max-w-7xl grid-cols-1 items-start gap-4 px-4 pb-16 sm:px-6 lg:grid-cols-2',
};

/** Regions the caller supplies as nodes rather than through `children`. */
export type TemplateRegionNodes = Partial<Record<RequiredRegion, ReactNode>>;

/**
 * What every template component accepts: the frame's contract, minus the
 * archetype and the layout, which the template itself owns.
 */
export type TemplatePageProps = Omit<TemplateFrameProps, 'template' | 'layout'>;

export interface TemplateFrameProps extends TemplateRegionNodes {
  /** The archetype. Supplies the region order, density and stamp placement. */
  template: PageTemplate;
  labels: TemplateLabels;
  path: string;
  state: DataState;
  total: number;
  /** Whether the gateway answered. Drives the live/unavailable badge. */
  ok: boolean;
  /**
   * Verified only on a real 2xx, exactly as `ResourcePage` does it with
   * `result.ok && verificationOf(result.data)`. The plan's standing rule is
   * real data or an explicit label, so this is never defaulted to `true`.
   */
  verified?: boolean;
  /** Second line of the state slot, e.g. `path · 51`, or "showing 3 of 51". */
  stateDetail?: string;
  /** `ResourcePage`'s own contract, reused rather than replaced. */
  children?: TemplateChildren;
  /**
   * Rendered immediately before the state slot and outside it.
   *
   * Only the archetypes whose surface must survive a failure use this. A tool's
   * input contract is the one thing a reader needs when a run fails — the
   * parameters are how they find out what to change — so it cannot live inside
   * `StateSlot`, which replaces its children on all four non-ready states.
   */
  prelude?: ReactNode;
  /** How `prelude` and the state slot sit together. `panels` is T07's signature. */
  preludeLayout?: 'stack' | 'panels';
  /** Layout signature. Defaults to a single column. */
  layout?: TemplateLayout;
  /** Rendered above the title. The page passes `<SiteNav locale={locale} />`. */
  nav?: ReactNode;
  /** The page's own `<h1>`. Required: a template never invents a heading. */
  title: string;
  /** Lead paragraph under the heading. */
  description?: string;
  /** Overrides the `<h1>` treatment, for the archetypes that differ. */
  titleClassName?: string;
}

/**
 * One labelled region. `data-region` is the contract the tests and the gate
 * read; it is also what makes a missing region visible in the DOM rather than
 * in a review comment.
 */
export function TemplateRegion({
  region,
  title,
  headingLevel: HeadingLevel = 'h2',
  className = '',
  children,
}: {
  region: RequiredRegion;
  title?: string;
  headingLevel?: 'h2' | 'h3';
  className?: string;
  children: ReactNode;
}) {
  return (
    <section
      data-region={region}
      aria-labelledby={title ? `region-${region}` : undefined}
      className={`min-w-0 ${className}`}
    >
      {title ? (
        <HeadingLevel id={`region-${region}`} className="field-label mb-2">
          {title}
        </HeadingLevel>
      ) : null}
      {children}
    </section>
  );
}

export function TemplateFrame({
  template,
  labels,
  path,
  state,
  total,
  ok,
  verified,
  stateDetail,
  children,
  prelude,
  preludeLayout = 'stack',
  layout = 'column',
  nav,
  title,
  titleClassName,
  description,
  ...rest
}: TemplateFrameProps) {
  const nodes: TemplateRegionNodes = rest;
  const gap = DENSITY_GAP[template.density];
  const anchor = template.provenance.anchor;

  /**
   * The stamp is placed, not requested. `provenance.anchor` names the region the
   * numbers live in, so a template cannot declare an anchor and then forget to
   * render the source: the frame renders it there.
   */
  const stamp = (
    <div
      data-provenance-region={anchor}
      className="mb-2 flex flex-wrap items-center justify-end gap-2"
    >
      <ProvenanceStamp source={path} label={labels.provenance} verified={verified} />
    </div>
  );

  /** Stamped regions get the stamp above their content. */
  const withStamp = (name: RequiredRegion, content: ReactNode): ReactNode =>
    name === anchor ? (
      <>
        {stamp}
        {content}
      </>
    ) : (
      content
    );

  /** True when the stamp cannot sit on the numbers and moves to the header. */
  const inHeader = anchor === 'data' && state !== 'ready';

  const region = (name: RequiredRegion): ReactNode => {
    const heading = labels.regions[name];

    if (name === 'title') {
      return (
        <header data-region="title" className="flex flex-col gap-3">
          {nav}
          <h1
            className={
              titleClassName ?? 'display text-3xl font-bold text-balance text-ink sm:text-4xl'
            }
          >
            {title}
          </h1>
          {description ? (
            <p className="max-w-2xl text-sm text-pretty text-ink-soft">{description}</p>
          ) : null}
        </header>
      );
    }

    if (name === 'status') {
      return (
        <div data-region="status" className="flex flex-wrap items-center gap-2">
          <Badge tone={ok ? 'success' : 'warn'} dot>
            {ok ? labels.live : labels.unavailable}
          </Badge>
        </div>
      );
    }

    // `state` and `data` are one unit: the slot reports the five states and its
    // children are the data region. Every archetype declares `state` immediately
    // before `data`, so the rendered order is the declared order.
    if (name === 'data') return null;
    if (name === 'state') {
      const slot = (
        <StateSlot
          state={state}
          labels={labels}
          density={SLOT_DENSITY[template.density]}
          detail={stateDetail}
        >
          <TemplateRegion region="data" className={gap}>
            {withStamp('data', renderTemplateChildren(children, { total, state, path }))}
          </TemplateRegion>
        </StateSlot>
      );
      return (
        <TemplateRegion region="state" title={labels.regions.state} className={gap}>
          {preludeLayout === 'panels' && prelude ? (
            <div className="grid gap-4 lg:grid-cols-[22rem_minmax(0,1fr)]">
              {prelude}
              {slot}
            </div>
          ) : (
            <>
              {prelude}
              {slot}
            </>
          )}
        </TemplateRegion>
      );
    }

    if (name === 'provenance') {
      // The stamp normally stands on the numbers, which means it lives inside
      // the data region. That region only exists when the contract answered, so
      // on any of the five non-ready states the stamp moves up here rather than
      // disappearing: a page that failed still has to say which contract failed.
      if (!inHeader && anchor !== 'provenance') return null;
      return (
        <TemplateRegion region="provenance" title={labels.regions.provenance} className={gap}>
          {stamp}
        </TemplateRegion>
      );
    }

    if (name === 'footer') {
      return (
        <TemplateRegion region="footer" title={labels.regions.footer} className={gap}>
          {labels.footer ? <p className="text-xs text-ink-faint">{labels.footer}</p> : null}
          {nodes.footer}
        </TemplateRegion>
      );
    }

    const content = nodes[name];
    if (content === undefined) return null;

    if (name === 'filters') {
      return (
        <TemplateRegion
          region="filters"
          title={heading}
          className="sticky start-0 top-16 z-30 rounded-m border border-line bg-surface p-3"
        >
          {withStamp('filters', content)}
        </TemplateRegion>
      );
    }

    return (
      <TemplateRegion region={name} title={heading} className={gap}>
        {withStamp(name, content)}
      </TemplateRegion>
    );
  };

  const rail: readonly RequiredRegion[] = (['actions', 'summary'] as const).filter(
    (name) => nodes[name] !== undefined,
  );
  const inRail = new Set<RequiredRegion>(rail);
  const flow = template.regions
    .filter((name) => !(layout === 'split' && inRail.has(name)))
    .map((name) => region(name))
    .filter((node) => node !== null && node !== undefined && node !== false);

  return (
    <main
      id="main"
      data-page-template={template.plan}
      data-density={template.density}
      className={`${LAYOUT_SHELL[layout]} ${gap}`}
    >
      {flow}
      {layout === 'split' && rail.length > 0 ? (
        <aside
          aria-label={labels.regions.actions ?? labels.regions.summary}
          className={`sticky top-20 flex flex-col ${gap}`}
        >
          {rail.map((name) => (
            <TemplateRegion key={name} region={name} title={labels.regions[name]} className={gap}>
              {withStamp(name, nodes[name])}
            </TemplateRegion>
          ))}
        </aside>
      ) : null}
    </main>
  );
}

export default TemplateFrame;
