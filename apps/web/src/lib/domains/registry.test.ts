import { describe, expect, it } from 'vitest';

import { hasRole } from '../auth/roles';
import {
  ADMIN_CONSOLE_ROLES,
  ADMIN_CONSOLE_ROUTE,
  DOMAIN_REGISTRY_VERSION,
  DOMAIN_ROUTES,
  findCapability,
  getDomainRoute,
  getScientificTool,
  HYDROMA_TOOLS_ROUTE,
  isCapabilityWired,
  isDeclaredScientificTool,
  isDomainId,
  isUssdMenuLanguage,
  resolveCapabilityState,
  resolveExecutionCapability,
  SCIENTIFIC_TOOL_IDS,
  SCIENTIFIC_TOOLS,
  SIMPLE_ACCESS_ROUTE,
  scientificToolParams,
  TELECOM_ROUTE,
  UNAVAILABLE_LABEL_KEY,
} from './registry';

describe('wave 3 domain registry', () => {
  it('registers one entry per wave 3 route surface', () => {
    expect(DOMAIN_REGISTRY_VERSION).toBe('2026-09-25');
    expect(DOMAIN_ROUTES.map((route) => route.id)).toEqual([
      'hydroma-tools',
      'admin-console',
      'research-workspace',
      'system-pwa-update',
      'system-webgpu-fallback',
      'inclusive-simple',
      'inclusive-telecom',
    ]);

    const ids = new Set(DOMAIN_ROUTES.map((route) => route.id));
    const patterns = new Set(DOMAIN_ROUTES.map((route) => route.pattern));
    expect(ids.size).toBe(DOMAIN_ROUTES.length);
    expect(patterns.size).toBe(DOMAIN_ROUTES.length);
  });

  it('keeps every heading and capability label on an existing message key', () => {
    const messageKey = /^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9]*)+$/;

    for (const route of DOMAIN_ROUTES) {
      expect(route.headingKey).toMatch(messageKey);
      expect(route.capabilities.length).toBeGreaterThan(0);
      for (const capability of route.capabilities) {
        expect(capability.labelKey).toMatch(messageKey);
        expect(capability.endpoint === null || capability.endpoint.startsWith('/api/v1/')).toBe(
          true,
        );
      }
    }
    expect(UNAVAILABLE_LABEL_KEY).toBe('statusLine.unavailable');
  });

  it('declares the shared unavailable state for every unwired capability', () => {
    const unwired = DOMAIN_ROUTES.flatMap((route) =>
      route.capabilities
        .filter((capability) => capability.endpoint === null)
        .map((capability) => `${route.id}:${capability.id}`),
    );

    // Research, PWA/WebGPU and the inclusive adapters have no contract yet.
    expect(unwired).toContain('hydroma-tools:tool-execution');
    expect(unwired).toContain('research-workspace:research-datasets');
    expect(unwired).toContain('system-pwa-update:pwa-update-state');
    expect(unwired).toContain('system-webgpu-fallback:compute-capability');
    expect(unwired).toContain('inclusive-simple:simple-sms');
    expect(unwired).toContain('inclusive-simple:simple-voice');
    expect(unwired).toContain('inclusive-telecom:telecom-sms-delivery');
    expect(unwired).toContain('admin-console:admin-overview');
  });

  it('resolves capability state without ever promoting an unwired contract', () => {
    const wired = findCapability(TELECOM_ROUTE, 'telecom-ussd-gateway');
    const unwired = findCapability(TELECOM_ROUTE, 'telecom-sms-delivery');

    expect(wired?.endpoint).toBe('/api/v1/ussd/status');
    expect(unwired?.endpoint).toBeNull();
    expect(isCapabilityWired(wired)).toBe(true);
    expect(isCapabilityWired(unwired)).toBe(false);
    expect(resolveCapabilityState(wired, true)).toBe('available');
    expect(resolveCapabilityState(wired, false)).toBe('unavailable');
    expect(resolveCapabilityState(unwired, true)).toBe('unavailable');
    expect(resolveCapabilityState(undefined, true)).toBe('unavailable');
  });

  it('exposes route, domain and capability lookup helpers', () => {
    expect(getDomainRoute('hydroma-tools')?.pattern).toBe('/:locale/hydroma/tools/[toolId]');
    expect(getDomainRoute('missing')).toBeUndefined();
    expect(findCapability(HYDROMA_TOOLS_ROUTE, 'tool-metadata')?.method).toBe('GET');
    expect(findCapability(HYDROMA_TOOLS_ROUTE, 'nope')).toBeUndefined();
    expect(isDomainId('inclusive')).toBe(true);
    expect(isDomainId('marketplace')).toBe(false);
  });

  it('gates the admin console behind an explicit role list', () => {
    expect(ADMIN_CONSOLE_ROUTE.access).toBe('role-gated');
    expect(ADMIN_CONSOLE_ROLES.length).toBeGreaterThan(0);
    expect(ADMIN_CONSOLE_ROLES.every((role) => hasRole(role, ADMIN_CONSOLE_ROLES))).toBe(true);
    expect(hasRole('farmer', ADMIN_CONSOLE_ROLES)).toBe(false);
    expect(hasRole('admin', ADMIN_CONSOLE_ROLES)).toBe(true);
  });

  it('keeps inclusive channels bound to real gateway endpoints only', () => {
    expect(findCapability(SIMPLE_ACCESS_ROUTE, 'simple-ussd-menu')?.endpoint).toBe(
      '/api/v1/ussd/menu/preview',
    );
    expect(findCapability(TELECOM_ROUTE, 'telecom-voice-health')?.endpoint).toBe(
      '/api/v1/voice/health',
    );
    expect(isUssdMenuLanguage('fa')).toBe(true);
    expect(isUssdMenuLanguage('de')).toBe(false);
  });
});

describe('scientific tool registry', () => {
  it('declares unique tool ids with a real engine module behind each one', () => {
    const ids = new Set(SCIENTIFIC_TOOL_IDS);
    const sources = new Set(SCIENTIFIC_TOOLS.map((tool) => tool.sourceOfTruth));

    expect(SCIENTIFIC_TOOLS.length).toBeGreaterThan(40);
    expect(ids.size).toBe(SCIENTIFIC_TOOLS.length);
    expect(sources.size).toBe(SCIENTIFIC_TOOLS.length);
    expect(SCIENTIFIC_TOOLS.every((tool) => tool.sourceOfTruth.startsWith('engine/hydroma/'))).toBe(
      true,
    );
    expect(SCIENTIFIC_TOOL_IDS).toContain('soil-health');
    expect(SCIENTIFIC_TOOL_IDS).toContain('swat-runner');
  });

  it('never declares an execution contract that the gateway does not expose', () => {
    expect(SCIENTIFIC_TOOLS.every((tool) => tool.executionEndpoint === null)).toBe(true);
    expect(getScientificTool('soil-health')?.domain).toBe('soil');
    expect(getScientificTool('unknown-tool')).toBeUndefined();
    expect(isDeclaredScientificTool('carbon-calculator')).toBe(true);
    expect(isDeclaredScientificTool('unknown-tool')).toBe(false);
  });

  it('builds one static param per declared tool', () => {
    const params = scientificToolParams();

    expect(params).toHaveLength(SCIENTIFIC_TOOLS.length);
    expect(params).toContainEqual({ toolId: 'et0-calculator' });
    expect(new Set(params.map((param) => param.toolId)).size).toBe(SCIENTIFIC_TOOLS.length);
  });

  it('marks execution available only when the live registry declares a path', () => {
    const declared = getScientificTool('soil-health');

    expect(resolveExecutionCapability(declared, null)).toBe('unavailable');
    expect(resolveExecutionCapability(declared, '   ')).toBe('unavailable');
    expect(resolveExecutionCapability(undefined, '/api/v1/soil/analyze')).toBe('unavailable');
    expect(resolveExecutionCapability(declared, '/api/v1/soil/analyze')).toBe('available');
  });
});
