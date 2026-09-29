import { describe, expect, it } from 'vitest';

import { PAGE_CATALOG } from '@/lib/domains/page-catalog';

import {
  createRouteContext,
  MANDATORY_REGIONS,
  matchTemplates,
  PAGE_TEMPLATE_COUNT,
  PAGE_TEMPLATES,
  REQUIRED_LABEL_KEYS,
  REQUIRED_STATES,
  requireTemplateForEntry,
  TEMPLATE_BY_ID,
  TEMPLATE_IDS,
  templateCoverage,
  templateForEntry,
} from './page-templates';

/**
 * The templates are a *partition* of the catalogue, not a list of suggestions.
 *
 * These assertions run against the real `PAGE_CATALOG` — all 600 entries read
 * from `src/lib/domains/page-catalog.ts` — so a route added without a chosen
 * archetype fails here, by name, rather than quietly inheriting a default.
 */

describe('the twelve templates of §4.4', () => {
  it('are all twelve, and a deletion fails', () => {
    // The count is asserted literally so removing T07 — the one the plan's gap
    // table row 6 is about — is a red test and not a quieter system.
    expect(PAGE_TEMPLATES).toHaveLength(PAGE_TEMPLATE_COUNT);
    expect(PAGE_TEMPLATE_COUNT).toBe(12);
    expect(TEMPLATE_IDS).toHaveLength(12);
    expect(PAGE_TEMPLATES.map((template) => template.id)).toEqual([...TEMPLATE_IDS]);
    expect(PAGE_TEMPLATES.map((template) => template.plan)).toEqual([
      'T01',
      'T02',
      'T03',
      'T04',
      'T05',
      'T06',
      'T07',
      'T08',
      'T09',
      'T10',
      'T11',
      'T12',
    ]);
  });

  it('index cleanly by id, with a unique plan code and a unique name', () => {
    for (const id of TEMPLATE_IDS) {
      expect(TEMPLATE_BY_ID[id], `TEMPLATE_BY_ID.${id}`).toBeDefined();
      expect(TEMPLATE_BY_ID[id].id).toBe(id);
    }
    expect(new Set(PAGE_TEMPLATES.map((t) => t.plan)).size).toBe(12);
    expect(new Set(PAGE_TEMPLATES.map((t) => t.name)).size).toBe(12);
    expect(new Set(PAGE_TEMPLATES.map((t) => t.planName)).size).toBe(12);
  });

  it('each carries a plan section, an intent and at least one declared surface', () => {
    for (const template of PAGE_TEMPLATES) {
      expect(template.planSection.length, `${template.plan} planSection`).toBeGreaterThan(0);
      expect(template.intent.length, `${template.plan} intent`).toBeGreaterThan(20);
      expect(template.surfaces.length, `${template.plan} surfaces`).toBeGreaterThan(0);
      for (const surface of template.surfaces) {
        expect(surface.trim().length, `${template.plan} surface copy`).toBeGreaterThan(0);
      }
    }
  });
});

describe('§4.5 state coverage is part of the type, and holds for all twelve', () => {
  it('every template declares exactly the five states, in order', () => {
    for (const template of PAGE_TEMPLATES) {
      expect(template.states, `${template.plan} states`).toEqual([
        'loading',
        'empty',
        'error',
        'partial',
        'offline',
      ]);
      expect(template.states, `${template.plan} state count`).toHaveLength(5);
      expect([...template.states].sort(), `${template.plan} state set`).toEqual(
        [...REQUIRED_STATES].sort(),
      );
    }
  });

  it('the required-state vocabulary is the five §4.5 names', () => {
    expect(REQUIRED_STATES).toEqual(['loading', 'empty', 'error', 'partial', 'offline']);
  });
});

describe('the provenance stamp is required, not remembered', () => {
  it('every template declares the provenance region and a placement for it', () => {
    for (const template of PAGE_TEMPLATES) {
      expect(template.provenance.required, `${template.plan} provenance.required`).toBe(true);
      expect(template.provenance.region, `${template.plan} provenance.region`).toBe('provenance');
      expect(
        ['data', 'summary', 'detail', 'actions'],
        `${template.plan} provenance.anchor`,
      ).toContain(template.provenance.anchor);
    }
  });

  it('the anchor is a region the template actually renders', () => {
    for (const template of PAGE_TEMPLATES) {
      expect(
        template.regions,
        `${template.plan} renders its provenance anchor "${template.provenance.anchor}"`,
      ).toContain(template.provenance.anchor);
    }
  });

  it('no template omits a mandatory region', () => {
    for (const template of PAGE_TEMPLATES) {
      for (const region of MANDATORY_REGIONS) {
        expect(template.regions, `${template.plan} is missing "${region}"`).toContain(region);
      }
    }
  });

  it('declares a density and a primary action that sits in the actions region', () => {
    for (const template of PAGE_TEMPLATES) {
      expect(['comfortable', 'compact', 'dense'], `${template.plan} density`).toContain(
        template.density,
      );
      if (template.primaryAction) {
        expect(template.primaryAction.region, `${template.plan} action region`).toBe('actions');
        expect(
          ['navigate', 'submit', 'run', 'retry', 'filter', 'print', 'export'],
          `${template.plan} action kind`,
        ).toContain(template.primaryAction.kind);
        expect(
          template.primaryAction.purpose.length,
          `${template.plan} action purpose`,
        ).toBeGreaterThan(0);
      }
    }
  });
});

describe('the catalogue is partitioned by the templates', () => {
  const coverage = templateCoverage(PAGE_CATALOG);

  it('reads the real catalogue, not a fixture', () => {
    expect(PAGE_CATALOG.length).toBeGreaterThan(0);
    expect(coverage.counts, 'every entry fell into the counts').toBeDefined();
  });

  it('no catalogue entry is left without a template', () => {
    // The failure message names the route, because "some pages have no layout"
    // is not actionable on 600 entries.
    expect(
      coverage.unmatched,
      `routes no template claims:\n  ${coverage.unmatched.join('\n  ')}`,
    ).toEqual([]);
  });

  it('no catalogue entry is claimed by two templates', () => {
    const report = coverage.ambiguous
      .map((entry) => `${entry.path} -> ${entry.templates.join(' + ')}`)
      .join('\n  ');
    expect(coverage.ambiguous, `routes claimed ambiguously:\n  ${report}`).toEqual([]);
  });

  it('every entry resolves to exactly one template through the public resolver', () => {
    for (const entry of PAGE_CATALOG) {
      const matched = matchTemplates(createRouteContext(entry));
      expect(matched, `${entry.path} matched ${matched.length} templates`).toHaveLength(1);
      expect(templateForEntry(entry), `${entry.path} did not resolve`).toBe(matched[0]);
    }
  });

  it('the counts add up to the catalogue, and no template is left empty', () => {
    const total = Object.values(coverage.counts).reduce((sum, count) => sum + count, 0);
    expect(total).toBe(PAGE_CATALOG.length);
    for (const id of TEMPLATE_IDS) {
      expect(coverage.counts[id], `${id} claims no catalogue entry`).toBeGreaterThan(0);
    }
  });
});

describe('a route added without a chosen template is caught by name', () => {
  it('names the path when nothing claims it', () => {
    // A real entry so the predicate runs over the real shape, then a path no
    // template claims. `requireTemplateForEntry` is what the generator calls,
    // so this is the error a developer would actually see.
    const unrouted = { ...PAGE_CATALOG[0], id: 'probe', path: '/zz-unrouted-probe' };
    expect(() => requireTemplateForEntry(unrouted)).toThrow(
      /no page template claims "\/zz-unrouted-probe"/,
    );
  });

  it('names every claimant when two templates overlap', () => {
    // No real route overlaps today — that is what the partition test above
    // asserts — so the ambiguity branch is reached by making one overlap
    // deliberately, then restoring it. A resolver that silently took the first
    // match is exactly the failure this gate exists to prevent, so the test
    // proves the refusal rather than only the absence.
    const listing = PAGE_CATALOG.find((entry) => entry.path === '/market/products');
    expect(listing, 'the marketplace listing is in the catalogue').toBeDefined();
    const probe = listing as (typeof PAGE_CATALOG)[number];

    const original = Object.getOwnPropertyDescriptor(TEMPLATE_BY_ID.instrument, 'matches');
    Object.defineProperty(TEMPLATE_BY_ID.instrument, 'matches', {
      value: (context: { path: string }) => context.path === '/market/products',
      configurable: true,
    });
    try {
      const claimed = matchTemplates(createRouteContext(probe)).map((template) => template.plan);
      expect(claimed, 'the probe is claimed by more than one template').toEqual(['T03', 'T07']);
      expect(templateForEntry(probe), 'the lenient resolver refuses to guess').toBeNull();
      expect(() => requireTemplateForEntry(probe)).toThrow(
        /claimed by more than one page template: T03\/discovery, T07\/instrument/,
      );
    } finally {
      if (original) Object.defineProperty(TEMPLATE_BY_ID.instrument, 'matches', original);
    }

    // The overlap really was the only thing that failed: once it is restored
    // the route resolves again, to the template that owns it.
    expect(requireTemplateForEntry(probe).plan).toBe('T03');
  });

  it('returns null from the lenient resolver rather than guessing', () => {
    const unrouted = { ...PAGE_CATALOG[0], id: 'probe', path: '/zz-unrouted-probe' };
    expect(templateForEntry(unrouted)).toBeNull();
  });
});

describe('the label contract the templates ask their caller for', () => {
  it('declares a key for every region a template can render', () => {
    const regions = new Set(
      PAGE_TEMPLATES.flatMap((template) => [...template.regions, template.provenance.region]),
    );
    const declared = new Set<string>(REQUIRED_LABEL_KEYS['templates.regions']);
    for (const region of regions) {
      expect(declared.has(region), `templates.regions is missing "${region}"`).toBe(true);
    }
  });

  it('declares a key for every state and every action kind', () => {
    for (const state of REQUIRED_STATES) {
      expect(REQUIRED_LABEL_KEYS['templates.states']).toContain(state);
    }
    for (const template of PAGE_TEMPLATES) {
      if (!template.primaryAction) continue;
      expect(
        REQUIRED_LABEL_KEYS['templates.actions'],
        `${template.plan} action kind "${template.primaryAction.kind}" has no key`,
      ).toContain(template.primaryAction.kind);
    }
  });
});
