import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import {
  MANDATORY_REGIONS,
  PAGE_TEMPLATE_COUNT,
  PAGE_TEMPLATES,
  REQUIRED_STATES,
  TEMPLATE_IDS,
  type TemplateId,
} from '@/lib/design/page-templates';

import {
  CoverPage,
  DashboardPage,
  DetailPage,
  DiscoveryPage,
  FlowPage,
  InstrumentPage,
  LearningPage,
  LedgerPage,
  LegalPage,
  NarrativePage,
  PAGE_TEMPLATE_COMPONENTS,
  ReportPage,
  SystemPage,
  templateDefinition,
} from './index';
import { frameProps, renderTemplate, templateLabels } from './templateTestHarness';

const COMPONENT_FOR: Record<TemplateId, unknown> = {
  cover: CoverPage,
  narrative: NarrativePage,
  discovery: DiscoveryPage,
  detail: DetailPage,
  flow: FlowPage,
  dashboard: DashboardPage,
  instrument: InstrumentPage,
  ledger: LedgerPage,
  legal: LegalPage,
  report: ReportPage,
  system: SystemPage,
  learning: LearningPage,
};

describe('the template layer', () => {
  it('exports exactly twelve, and a thirteenth is a compile error here', () => {
    expect(TEMPLATE_IDS).toHaveLength(PAGE_TEMPLATE_COUNT);
    expect(Object.keys(PAGE_TEMPLATE_COMPONENTS)).toHaveLength(PAGE_TEMPLATE_COUNT);
    expect(Object.keys(COMPONENT_FOR)).toHaveLength(PAGE_TEMPLATE_COUNT);
  });

  it('gives every archetype a component, keyed by the plan id order', () => {
    expect(Object.keys(PAGE_TEMPLATE_COMPONENTS)).toEqual([...TEMPLATE_IDS]);
    for (const id of TEMPLATE_IDS) {
      expect(PAGE_TEMPLATE_COMPONENTS[id], `${id} has no component`).toBeDefined();
      expect(COMPONENT_FOR[id], `${id} was not tested`).toBeDefined();
    }
  });

  it('hands back the archetype definition for a plan id', () => {
    for (const id of TEMPLATE_IDS) {
      expect(templateDefinition(id).id).toBe(id);
      expect(templateDefinition(id).plan).toBe(PAGE_TEMPLATES[TEMPLATE_IDS.indexOf(id)].plan);
    }
  });

  it('is not a client island: the templates themselves are server components', () => {
    // A layout that carries `'use client'` ships its whole subtree to the
    // browser as JavaScript. The plan's performance budget rules that out for
    // chrome, and a grep of the sources is the only check that cannot be
    // satisfied by a runtime value.
    const files = [
      'CoverPage',
      'DashboardPage',
      'DetailPage',
      'DiscoveryPage',
      'FlowPage',
      'InstrumentPage',
      'LedgerPage',
      'LegalPage',
      'LearningPage',
      'NarrativePage',
      'ReportPage',
      'SystemPage',
      'TemplateFrame',
    ];
    const dir = dirname(fileURLToPath(import.meta.url));
    for (const name of files) {
      const source = readFileSync(join(dir, `${name}.tsx`), 'utf8');
      expect(source, `${name} is a client island`).not.toMatch(/^\s*['"]use client['"]/m);
    }
  });

  it('declares, for every archetype, the regions the frame knows how to render', () => {
    const renderable = new Set<unknown>([
      'title',
      'status',
      'provenance',
      'filters',
      'state',
      'data',
      'navigation',
      'actions',
      'summary',
      'detail',
      'notes',
      'print',
      'footer',
    ]);
    for (const template of PAGE_TEMPLATES) {
      for (const region of template.regions) {
        expect(renderable.has(region), `${template.plan} declares unknown region "${region}"`).toBe(
          true,
        );
      }
    }
  });

  it('puts `state` immediately before `data` everywhere, so the DOM order is the declared order', () => {
    // The frame renders the state slot and nests the data region inside it, so
    // this ordering is what keeps §4.5's state from appearing below the data it
    // is a state of.
    for (const template of PAGE_TEMPLATES) {
      const state = template.regions.indexOf('state');
      expect(state, `${template.plan} has no state region`).toBeGreaterThanOrEqual(0);
      expect(template.regions[state + 1], `${template.plan} must declare data after state`).toBe(
        'data',
      );
    }
  });

  it('renders the labels it is given and invents none of its own', () => {
    // The whole reason `TemplateLabels` is a prop rather than a constant: a
    // component library that carries English cannot be translated, which is the
    // defect the 53 public pages had. So a caller renaming a region heading must
    // see that exact string, and nothing else may appear in its place.
    const view = renderTemplate(
      <DetailPage
        {...frameProps()}
        labels={templateLabels(
          { live: 'DER ECHTE DATEN', unavailable: 'NICHT ERREICHBAR' },
          { actions: 'HANDELN', summary: 'FAKTEN' },
        )}
        actions={<div>BUY</div>}
        summary={<div>PRICE</div>}
      />,
    );
    expect(view.text()).toContain('HANDELN');
    expect(view.text()).toContain('FAKTEN');
    expect(view.text()).toContain('DER ECHTE DATEN');
    expect(view.text()).not.toContain('ACTIONS');
    expect(view.region('actions')?.getAttribute('aria-labelledby')).toBe('region-actions');
  });

  it('keeps the mandatory regions and the five states on every archetype', () => {
    for (const template of PAGE_TEMPLATES) {
      for (const region of MANDATORY_REGIONS) {
        expect(template.regions, `${template.plan} is missing "${region}"`).toContain(region);
      }
      expect([...template.states].sort(), `${template.plan} states`).toEqual(
        [...REQUIRED_STATES].sort(),
      );
    }
  });
});
