import { describe, expect, it } from 'vitest';

import {
  getResearchPanel,
  isExperimentCapabilityWired,
  isPanelSourceWired,
  isResearchExperimentId,
  RESEARCH_CITATIONS_ENDPOINT,
  RESEARCH_DATASETS_ENDPOINT,
  RESEARCH_DOI_ENDPOINT,
  RESEARCH_PANEL_IDS,
  RESEARCH_ROUTE_ID,
  RESEARCH_WORKSPACE_PANELS,
  researchCapability,
  resolvePanelState,
  resolveSourceState,
} from './registry';

describe('research workspace contract', () => {
  it('covers datasets, runs, validation and provenance exactly once', () => {
    expect(RESEARCH_PANEL_IDS).toEqual(['datasets', 'runs', 'validation', 'provenance']);
    expect(RESEARCH_ROUTE_ID).toBe('research-workspace');
  });

  it('keeps every heading and detail on an existing message key', () => {
    const messageKey = /^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9]*)+$/;

    for (const panel of RESEARCH_WORKSPACE_PANELS) {
      expect(panel.headingKey).toMatch(messageKey);
      expect(panel.detailKey).toMatch(messageKey);
      expect(panel.capabilityId).not.toBe('');
      expect(panel.sourceEndpoint === null || panel.sourceEndpoint.startsWith('/api/v1/')).toBe(
        true,
      );
    }
  });

  it('only binds endpoints the gateway really registers', () => {
    expect(RESEARCH_DATASETS_ENDPOINT).toBe('/api/v1/science/datasets');
    expect(RESEARCH_CITATIONS_ENDPOINT).toBe('/api/v1/science/citations/index');
    expect(RESEARCH_DOI_ENDPOINT).toBe('/api/v1/science/zenodo/status');
    expect(getResearchPanel('datasets')?.sourceEndpoint).toBe(RESEARCH_DATASETS_ENDPOINT);
    expect(getResearchPanel('provenance')?.sourceEndpoint).toBe(RESEARCH_CITATIONS_ENDPOINT);
    expect(getResearchPanel('runs')?.sourceEndpoint).toBeNull();
    expect(getResearchPanel('missing')).toBeUndefined();
  });

  it('never promotes an experiment record while the capability is unwired', () => {
    expect(researchCapability('research-experiments')?.endpoint).toBeNull();
    expect(researchCapability('research-datasets')?.endpoint).toBeNull();
    expect(researchCapability('research-citations')?.endpoint).toBeNull();
    expect(researchCapability('research-missing')).toBeUndefined();
    expect(isExperimentCapabilityWired('research-experiments')).toBe(false);
    expect(isExperimentCapabilityWired('research-missing')).toBe(false);
  });

  it('collapses every unwired or failing panel to unavailable', () => {
    const runs = getResearchPanel('runs');
    const datasets = getResearchPanel('datasets');

    expect(runs).toBeDefined();
    expect(datasets).toBeDefined();
    if (!runs || !datasets) throw new Error('panels missing');

    expect(isPanelSourceWired(runs)).toBe(false);
    expect(isPanelSourceWired(datasets)).toBe(true);
    expect(resolvePanelState(runs, true)).toBe('unavailable');
    expect(resolvePanelState(datasets, false)).toBe('unavailable');
    expect(resolvePanelState(datasets, true)).toBe('available');
    expect(resolveSourceState(RESEARCH_DOI_ENDPOINT, true)).toBe('available');
    expect(resolveSourceState(RESEARCH_DOI_ENDPOINT, false)).toBe('unavailable');
    expect(resolveSourceState(null, true)).toBe('unavailable');
  });

  it('accepts only bounded, path-safe experiment ids', () => {
    expect(isResearchExperimentId('exp-2026-09-25')).toBe(true);
    expect(isResearchExperimentId('Exp_42.a')).toBe(true);
    expect(isResearchExperimentId('')).toBe(false);
    expect(isResearchExperimentId('-leading')).toBe(false);
    expect(isResearchExperimentId('a'.repeat(65))).toBe(false);
    expect(isResearchExperimentId('../../etc/passwd')).toBe(false);
    expect(isResearchExperimentId('exp/1')).toBe(false);
  });
});
