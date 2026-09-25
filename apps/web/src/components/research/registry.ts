import {
  type DomainCapability,
  type DomainCapabilityState,
  findCapability,
  isCapabilityWired,
  RESEARCH_WORKSPACE_ROUTE,
} from '@/lib/domains/registry';

/**
 * Research workspace contract — Tier 0 of
 * `docs/frontend/WORLD_CLASS_BENCHMARK_2026-09-25.md`.
 *
 * The gateway registers no experiment, run, DOI or validation endpoint, so
 * every panel that would hold an experiment record collapses to `unavailable`.
 * The three endpoints below are the only real science contracts the gateway
 * exposes; they may never be used to invent a run, a dataset row or a DOI.
 */
export const RESEARCH_DATASETS_ENDPOINT = '/api/v1/science/datasets';
export const RESEARCH_CITATIONS_ENDPOINT = '/api/v1/science/citations/index';
export const RESEARCH_DOI_ENDPOINT = '/api/v1/science/zenodo/status';

export const RESEARCH_ROUTE_ID = RESEARCH_WORKSPACE_ROUTE.id;
export const RESEARCH_ROUTE_PATTERN = RESEARCH_WORKSPACE_ROUTE.pattern;

export type ResearchPanelId = 'datasets' | 'runs' | 'validation' | 'provenance';

export interface ResearchWorkspacePanel {
  id: ResearchPanelId;
  /** `namespace.key` message key for the tab label and the panel heading. */
  headingKey: string;
  /** `namespace.key` message key for the one-sentence panel explanation. */
  detailKey: string;
  /** Capability of `RESEARCH_WORKSPACE_ROUTE` that governs experiment records. */
  capabilityId: string;
  /** Registered gateway endpoint backing the panel, or `null` when none exists. */
  sourceEndpoint: string | null;
}

export const RESEARCH_WORKSPACE_PANELS: readonly ResearchWorkspacePanel[] = [
  {
    id: 'datasets',
    headingKey: 'public.science.evidenceBase.evidenceCatalog',
    detailKey: 'statusPage.subtitle',
    capabilityId: 'research-datasets',
    sourceEndpoint: RESEARCH_DATASETS_ENDPOINT,
  },
  {
    id: 'runs',
    headingKey: 'statusPage.result',
    detailKey: 'market.template.unavailableDescription',
    capabilityId: 'research-experiments',
    sourceEndpoint: null,
  },
  {
    id: 'validation',
    headingKey: 'common.evidence',
    detailKey: 'evidence.lead',
    capabilityId: 'research-citations',
    sourceEndpoint: null,
  },
  {
    id: 'provenance',
    headingKey: 'trust.title',
    detailKey: 'trust.lead',
    capabilityId: 'research-citations',
    sourceEndpoint: RESEARCH_CITATIONS_ENDPOINT,
  },
] as const;

export const RESEARCH_PANEL_IDS: readonly ResearchPanelId[] = RESEARCH_WORKSPACE_PANELS.map(
  (panel) => panel.id,
);

export function getResearchPanel(id: string): ResearchWorkspacePanel | undefined {
  return RESEARCH_WORKSPACE_PANELS.find((panel) => panel.id === id);
}

export function researchCapability(capabilityId: string): DomainCapability | undefined {
  return findCapability(RESEARCH_WORKSPACE_ROUTE, capabilityId);
}

/** Experiment-scoped records stay unavailable while their capability is unwired. */
export function isExperimentCapabilityWired(capabilityId: string): boolean {
  return isCapabilityWired(researchCapability(capabilityId));
}

export function isPanelSourceWired(panel: ResearchWorkspacePanel): boolean {
  return panel.sourceEndpoint !== null;
}

/** A panel may only report live records when its registered endpoint answered. */
export function resolvePanelState(
  panel: ResearchWorkspacePanel,
  ok: boolean,
): DomainCapabilityState {
  return isPanelSourceWired(panel) && ok ? 'available' : 'unavailable';
}

/** Same rule for a bare endpoint, used by the research index source list. */
export function resolveSourceState(endpoint: string | null, ok: boolean): DomainCapabilityState {
  return endpoint !== null && ok ? 'available' : 'unavailable';
}

/** Bounded, locale-independent and path-safe experiment identifiers. */
export const RESEARCH_EXPERIMENT_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;

export function isResearchExperimentId(value: string): boolean {
  return RESEARCH_EXPERIMENT_ID_PATTERN.test(value);
}
