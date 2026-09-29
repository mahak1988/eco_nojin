import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import { expect } from 'vitest';

import type { DataState } from '@/components/ui/StateSlot';
import type { RequiredRegion, TemplateLabels } from '@/lib/design/page-templates';

/**
 * One fixture for all twelve template tests.
 *
 * Every string is a placeholder on purpose. The point of the templates is that
 * they hold no copy of their own — a component library that carries English
 * cannot be translated, which is the defect the 53 public pages had. So the
 * harness proves the plumbing with obviously-fake strings, and the real copy
 * arrives from `messages/<locale>.json` through `getTranslations`.
 */

/** §4.5: the five states every data-bearing surface must be able to show. */
export const ALL_STATES: readonly DataState[] = [
  'loading',
  'empty',
  'error',
  'partial',
  'offline',
] as const;

/** Every region name the frame can render, so a region rename fails loudly. */
export const ALL_REGIONS: readonly RequiredRegion[] = [
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
] as const;

function regionLabels(
  overrides: Partial<Record<RequiredRegion, string>> = {},
): Partial<Record<RequiredRegion, string>> {
  return Object.fromEntries([
    ...ALL_REGIONS.map((region) => [region, region.toUpperCase()]),
    ...Object.entries(overrides),
  ]) as Partial<Record<RequiredRegion, string>>;
}

export function templateLabels(
  overrides: Partial<TemplateLabels> = {},
  regions: Partial<Record<RequiredRegion, string>> = {},
): TemplateLabels {
  return {
    // `StateLabels`: the same five-state copy `ResourcePage.resourceLabels()`
    // builds today, so the states need no new message namespace.
    loading: 'LOADING',
    empty: 'EMPTY',
    error: 'ERROR',
    offline: 'OFFLINE',
    partial: 'PARTIAL',
    action: 'RETRY',
    provenance: 'PROVENANCE',
    live: 'LIVE',
    unavailable: 'UNAVAILABLE',
    primaryAction: 'DO',
    footer: 'market-product',
    ...overrides,
    regions: regionLabels(regions),
  };
}

export interface FrameOptions {
  state?: DataState;
  ok?: boolean;
  total?: number;
  verified?: boolean;
}

/** The base props every template test needs, for one state. */
export function frameProps({
  state = 'ready',
  ok = true,
  total = 3,
  verified = true,
}: FrameOptions = {}) {
  return {
    title: 'Page title',
    description: 'Lead paragraph.',
    labels: templateLabels(),
    path: '/api/v1/example',
    state,
    total,
    ok,
    verified,
    stateDetail: '/api/v1/example · 3',
    children: <p>DATA</p>,
  };
}

/** Render a template element and hand back the queries the tests read. */
export function renderTemplate(element: ReactElement) {
  const view = render(element);
  const q = (selector: string) => view.container.querySelector(selector);
  return {
    ...view,
    q,
    region: (name: RequiredRegion) => q(`[data-region="${name}"]`),
    stampIn: (name: RequiredRegion) => q(`[data-region="${name}"] [data-provenance]`),
    text: () => view.container.textContent ?? '',
  };
}

export type TemplateView = ReturnType<typeof renderTemplate>;

/**
 * Renders one element per §4.5 state and returns the views, so each of the
 * twelve tests asserts the same five rather than inventing its own list.
 */
export function renderAllStates(build: (state: DataState) => ReactElement): TemplateView[] {
  return ALL_STATES.map((state) => renderTemplate(build(state)));
}

/** The two things §4.5 makes non-negotiable on every archetype. */
export function expectFiveStates(views: readonly TemplateView[]) {
  expect(ALL_STATES).toHaveLength(5);
  for (const view of views) {
    expect(view.text().length, 'a state rendered nothing at all').toBeGreaterThan(0);
    expect(view.region('title'), 'every state keeps the title region').not.toBeNull();
  }
}

/** One `<h1>`, and it comes first. */
export function expectHeadingOrder(container: Element) {
  const headings = [...container.querySelectorAll('h1,h2,h3')];
  expect(headings[0]?.tagName, 'the first heading must be the h1').toBe('H1');
  expect(container.querySelectorAll('h1')).toHaveLength(1);
}
