import type { GlobalRole } from '@/lib/auth/roles';

/**
 * Wave 3 domain route registry — the single source of truth shared by the
 * Hydroma, Admin, Research, System and Inclusive route surfaces.
 *
 * Two rules are encoded here so that no page has to invent state:
 *
 * 1. A capability declares a real API gateway endpoint, or `endpoint: null`
 *    when no contract exists yet. Pages must render `status: 'unavailable'`
 *    for every `null` endpoint and must never substitute a number, a mock
 *    value or a `verified` provenance claim.
 * 2. Every visible string is an i18n key (`headingKey`, `labelKey`), so route
 *    files cannot hard-code copy.
 */
export const DOMAIN_REGISTRY_VERSION = '2026-09-25';

export type DomainId = 'hydroma' | 'admin' | 'research' | 'system' | 'inclusive';

export type DomainRouteKind =
  | 'scientific-tool'
  | 'console'
  | 'workspace'
  | 'system-state'
  | 'channel';

export type DomainAccess = 'public' | 'authenticated' | 'role-gated' | 'internal';

export type DomainCapabilityState = 'available' | 'unavailable';

export interface DomainCapability {
  id: string;
  /** `namespace.key` message key for the capability label. */
  labelKey: string;
  method: 'GET' | 'POST';
  /** Real gateway endpoint, or `null` while the contract is unimplemented. */
  endpoint: string | null;
}

export interface DomainRoute {
  id: string;
  domain: DomainId;
  pattern: string;
  kind: DomainRouteKind;
  access: DomainAccess;
  allowedRoles: readonly GlobalRole[];
  owner: string;
  sourceOfTruth: string;
  /** `namespace.key` message key for the page heading. */
  headingKey: string;
  capabilities: readonly DomainCapability[];
}

/** Shared label keys so every route reports the same state the same way. */
export const UNAVAILABLE_LABEL_KEY = 'statusLine.unavailable';
export const REAL_DATA_LABEL_KEY = 'statusLine.realData';
export const EMPTY_TITLE_LABEL_KEY = 'learn.emptyTitle';
export const EMPTY_DETAIL_LABEL_KEY = 'learn.emptyDesc';
export const CONTRACT_LABEL_KEY = 'market.template.contractTitle';
export const CONTRACT_DETAIL_LABEL_KEY = 'market.template.contractDescription';
export const UNAVAILABLE_TITLE_KEY = 'market.template.unavailableTitle';
export const UNAVAILABLE_DETAIL_KEY = 'market.template.unavailableDescription';
export const NEXT_LABEL_KEY = 'market.template.nextTitle';
export const NEXT_DETAIL_KEY = 'market.template.nextDescription';
export const SOURCE_LABEL_KEY = 'market.template.source';
export const RESULT_LABEL_KEY = 'statusPage.result';
export const STATE_LABEL_KEY = 'statusPage.state';
export const ENDPOINT_LABEL_KEY = 'statusPage.endpoint';
export const SERVICE_LABEL_KEY = 'statusPage.service';
export const METRIC_LABEL_KEY = 'statusPage.label';
export const RETRY_LABEL_KEY = 'common.retry';
export const LIVE_LABEL_KEY = 'common.live';
export const BACK_LABEL_KEY = 'common.back';
export const VIEW_LABEL_KEY = 'common.view';
export const EVIDENCE_LABEL_KEY = 'common.evidence';
export const LIMITS_LABEL_KEY = 'common.limits';
export const NEXT_STEP_LABEL_KEY = 'common.next';

/** Deny-by-default: every one of these roles is required by the admin console. */
export const ADMIN_CONSOLE_ROLES: readonly GlobalRole[] = [
  'admin',
  'security_admin',
  'content_admin',
  'user_admin',
];

export const HYDROMA_TOOLS_ROUTE = {
  id: 'hydroma-tools',
  domain: 'hydroma',
  pattern: '/:locale/hydroma/tools/[toolId]',
  kind: 'scientific-tool',
  access: 'public',
  allowedRoles: [],
  owner: 'hydroma',
  sourceOfTruth: 'services/api_gateway/routers/tool_registry.py',
  headingKey: 'science.title',
  capabilities: [
    {
      id: 'tool-metadata',
      labelKey: 'science.modelsTitle',
      method: 'GET',
      endpoint: '/api/v1/tool-registry/{tool_id}',
    },
    {
      id: 'tool-execution',
      labelKey: RESULT_LABEL_KEY,
      method: 'POST',
      // No per-tool execution contract is registered: the web layer never
      // posts inputs, so results stay unavailable instead of being faked.
      endpoint: null,
    },
    {
      id: 'cpp-kernel-status',
      labelKey: 'science.kernels',
      method: 'GET',
      endpoint: '/api/v1/models/cpp-status',
    },
  ],
} satisfies DomainRoute;

export const ADMIN_CONSOLE_ROUTE = {
  id: 'admin-console',
  domain: 'admin',
  pattern: '/:locale/admin',
  kind: 'console',
  access: 'role-gated',
  allowedRoles: ADMIN_CONSOLE_ROLES,
  owner: 'platform-admin',
  sourceOfTruth: 'services/api_gateway/routers/admin_overview.py',
  headingKey: 'statusPage.title',
  capabilities: [
    {
      id: 'platform-health',
      labelKey: SERVICE_LABEL_KEY,
      method: 'GET',
      endpoint: '/api/v1/platform/health',
    },
    {
      id: 'platform-stats',
      labelKey: 'statusPage.landscapes',
      method: 'GET',
      endpoint: '/api/v1/platform/stats',
    },
    {
      // /api/v1/admin/overview exists upstream but answers with hard-coded
      // placeholder counters, so the web layer reports it as unavailable.
      id: 'admin-overview',
      labelKey: 'platformOverview.title',
      method: 'GET',
      endpoint: null,
    },
    {
      id: 'admin-channel-health',
      labelKey: 'statusPage.cpp',
      method: 'GET',
      endpoint: null,
    },
    {
      id: 'admin-audit',
      labelKey: 'trust.title',
      method: 'GET',
      endpoint: null,
    },
  ],
} satisfies DomainRoute;

export const RESEARCH_WORKSPACE_ROUTE = {
  id: 'research-workspace',
  domain: 'research',
  pattern: '/:locale/research',
  kind: 'workspace',
  access: 'authenticated',
  allowedRoles: ['researcher', 'advisor', 'organization', 'admin'],
  owner: 'research-platform',
  sourceOfTruth: 'master-plan/research-context',
  headingKey: 'evidence.title',
  capabilities: [
    {
      id: 'research-datasets',
      labelKey: 'evidence.title',
      method: 'GET',
      // No research API surface exists yet (datasets, experiments, DOI).
      endpoint: null,
    },
    {
      id: 'research-experiments',
      labelKey: 'platformOverview.itemScience',
      method: 'GET',
      endpoint: null,
    },
    {
      id: 'research-citations',
      labelKey: 'trust.title',
      method: 'GET',
      endpoint: null,
    },
  ],
} satisfies DomainRoute;

export const SYSTEM_PWA_UPDATE_ROUTE = {
  id: 'system-pwa-update',
  domain: 'system',
  pattern: '/:locale/system/pwa-update',
  kind: 'system-state',
  access: 'internal',
  allowedRoles: [],
  owner: 'platform-operations',
  sourceOfTruth: 'apps/web/src/app/sw.ts',
  headingKey: 'public.channels.webPwa',
  capabilities: [
    {
      // Service-worker lifecycle is browser-local; there is nothing to fetch.
      id: 'pwa-update-state',
      labelKey: 'offline.code',
      method: 'GET',
      endpoint: null,
    },
    {
      id: 'pwa-cached-assets',
      labelKey: 'offline.title',
      method: 'GET',
      endpoint: null,
    },
  ],
} satisfies DomainRoute;

export const SYSTEM_WEBGPU_FALLBACK_ROUTE = {
  id: 'system-webgpu-fallback',
  domain: 'system',
  pattern: '/:locale/system/webgpu-fallback',
  kind: 'system-state',
  access: 'internal',
  allowedRoles: [],
  owner: 'platform-operations',
  sourceOfTruth: 'engine/hydroma/cpp_bridge',
  headingKey: 'statusPage.cpp',
  capabilities: [
    {
      // GPU/WebGPU capability is a client-side probe, not a server contract.
      id: 'compute-capability',
      labelKey: 'statusPage.cpp',
      method: 'GET',
      endpoint: null,
    },
    {
      id: 'cpp-kernel-status',
      labelKey: 'science.kernels',
      method: 'GET',
      endpoint: '/api/v1/models/cpp-status',
    },
  ],
} satisfies DomainRoute;

export const SIMPLE_ACCESS_ROUTE = {
  id: 'inclusive-simple',
  domain: 'inclusive',
  pattern: '/:locale/simple',
  kind: 'channel',
  access: 'public',
  allowedRoles: [],
  owner: 'platform-operations',
  sourceOfTruth: 'services/api_gateway/routers/ussd.py',
  headingKey: 'public.channels.title',
  capabilities: [
    {
      id: 'simple-ussd-menu',
      labelKey: 'public.channels.ussd',
      method: 'GET',
      endpoint: '/api/v1/ussd/menu/preview',
    },
    {
      id: 'simple-ussd-gateway',
      labelKey: 'public.channels.sms',
      method: 'GET',
      endpoint: '/api/v1/ussd/status',
    },
    {
      id: 'simple-sms',
      labelKey: 'public.channels.sms',
      method: 'GET',
      // USSD/SMS delivery needs a telecom gateway; no delivery status exists.
      endpoint: null,
    },
    {
      id: 'simple-voice',
      labelKey: 'public.channels.voice',
      method: 'GET',
      // Voice is an independent adapter, never a fake Next.js route.
      endpoint: null,
    },
  ],
} satisfies DomainRoute;

export const TELECOM_ROUTE = {
  id: 'inclusive-telecom',
  domain: 'inclusive',
  pattern: '/:locale/telecom',
  kind: 'channel',
  access: 'public',
  allowedRoles: [],
  owner: 'platform-operations',
  sourceOfTruth: 'services/api_gateway/routers/voice.py',
  headingKey: 'offline.title',
  capabilities: [
    {
      id: 'telecom-ussd-gateway',
      labelKey: 'public.channels.ussd',
      method: 'GET',
      endpoint: '/api/v1/ussd/status',
    },
    {
      id: 'telecom-voice-gateway',
      labelKey: 'public.channels.voice',
      method: 'GET',
      endpoint: '/api/v1/voice/status',
    },
    {
      id: 'telecom-voice-health',
      labelKey: SERVICE_LABEL_KEY,
      method: 'GET',
      endpoint: '/api/v1/voice/health',
    },
    {
      id: 'telecom-sms-delivery',
      labelKey: 'public.channels.sms',
      method: 'GET',
      endpoint: null,
    },
  ],
} satisfies DomainRoute;

export const DOMAIN_ROUTES = [
  HYDROMA_TOOLS_ROUTE,
  ADMIN_CONSOLE_ROUTE,
  RESEARCH_WORKSPACE_ROUTE,
  SYSTEM_PWA_UPDATE_ROUTE,
  SYSTEM_WEBGPU_FALLBACK_ROUTE,
  SIMPLE_ACCESS_ROUTE,
  TELECOM_ROUTE,
] as const satisfies readonly DomainRoute[];

export function getDomainRoute(id: string): DomainRoute | undefined {
  return DOMAIN_ROUTES.find((route) => route.id === id);
}

export function isDomainId(value: string): value is DomainId {
  return DOMAIN_ROUTES.some((route) => route.domain === value);
}

export function findCapability(
  route: DomainRoute,
  capabilityId: string,
): DomainCapability | undefined {
  return route.capabilities.find((capability) => capability.id === capabilityId);
}

/** A capability may only be shown as available when a contract exists for it. */
export function isCapabilityWired(capability: DomainCapability | undefined): boolean {
  return capability !== undefined && capability.endpoint !== null;
}

/**
 * Resolves the state a page may render. An unwired capability, a missing
 * capability or a failed request always collapse to `unavailable`.
 */
export function resolveCapabilityState(
  capability: DomainCapability | undefined,
  ok: boolean,
): DomainCapabilityState {
  return isCapabilityWired(capability) && ok ? 'available' : 'unavailable';
}

export type ScientificToolDomain =
  | 'water'
  | 'soil'
  | 'climate'
  | 'carbon'
  | 'crop'
  | 'modeling'
  | 'decision';

export type ScientificToolCategory = 'algorithm' | 'model' | 'service' | 'workflow';

export interface ScientificToolDeclaration {
  id: string;
  domain: ScientificToolDomain;
  category: ScientificToolCategory;
  /** Engine module that implements the tool. */
  sourceOfTruth: string;
  /**
   * Execution contract for this tool. The engine has no published per-tool
   * execution route, so the whole registry stays `null` until one exists.
   */
  executionEndpoint: string | null;
}

export const SCIENTIFIC_TOOLS: readonly ScientificToolDeclaration[] = [
  // Water and hydrology
  {
    id: 'hydrology-fallback',
    domain: 'water',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/hydrology_fallback.py',
    executionEndpoint: null,
  },
  {
    id: 'hydrology-fast',
    domain: 'water',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/hydrology_fast.py',
    executionEndpoint: null,
  },
  {
    id: 'indices-fallback',
    domain: 'water',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/indices_fallback.py',
    executionEndpoint: null,
  },
  {
    id: 'indices-fast',
    domain: 'water',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/indices_fast.py',
    executionEndpoint: null,
  },
  {
    id: 'topographic-calculations',
    domain: 'water',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/utils/topographic_calcs.py',
    executionEndpoint: null,
  },
  {
    id: 'water-quality',
    domain: 'water',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/water/quality.py',
    executionEndpoint: null,
  },
  {
    id: 'watershed-calculator',
    domain: 'water',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/watershed/calculator.py',
    executionEndpoint: null,
  },
  {
    id: 'irrigation-scheduler',
    domain: 'water',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/irrigation/scheduler.py',
    executionEndpoint: null,
  },
  {
    id: 'groundwater-model',
    domain: 'water',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/groundwater/models.py',
    executionEndpoint: null,
  },
  {
    id: 'groundwater-service',
    domain: 'water',
    category: 'service',
    sourceOfTruth: 'engine/hydroma/groundwater/service.py',
    executionEndpoint: null,
  },
  {
    id: 'hecras-simulation',
    domain: 'water',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/simulation/hecras.py',
    executionEndpoint: null,
  },
  {
    id: 'weap-simulation',
    domain: 'water',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/simulation/weap.py',
    executionEndpoint: null,
  },
  {
    id: 'hydroma-core',
    domain: 'water',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/core/core.py',
    executionEndpoint: null,
  },

  // Soil
  {
    id: 'soil-physics-fast',
    domain: 'soil',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/soil_physics_fast.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-physics-fallback',
    domain: 'soil',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/cpp_bridge/soil_physics_fallback.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-physics',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/physics.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-chemistry',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/chemistry.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-health',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/health.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-salinity',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/salinity.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-taxonomy',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/taxonomy.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-texture',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/texture.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-water-retention',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/water_retention.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-pedotransfer',
    domain: 'soil',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/soil/pedotransfer.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-recommendations',
    domain: 'soil',
    category: 'service',
    sourceOfTruth: 'engine/hydroma/soil/recommendations.py',
    executionEndpoint: null,
  },

  // Climate
  {
    id: 'et0-calculator',
    domain: 'climate',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/climate/et_calculator.py',
    executionEndpoint: null,
  },
  {
    id: 'climate-adaptive-phenology',
    domain: 'climate',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/climate_adaptive_phenology.py',
    executionEndpoint: null,
  },
  {
    id: 'dynamic-stress-engine',
    domain: 'climate',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/dynamic_stress_engine.py',
    executionEndpoint: null,
  },
  {
    id: 'multi-stress-engine',
    domain: 'climate',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/multi_stress_engine.py',
    executionEndpoint: null,
  },
  {
    id: 'seed-optimization',
    domain: 'climate',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/seed_optimization_engine.py',
    executionEndpoint: null,
  },
  {
    id: 'soil-degradation-model',
    domain: 'climate',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/soil_degradation_model.py',
    executionEndpoint: null,
  },
  {
    id: 'uncertainty-knowledge',
    domain: 'climate',
    category: 'service',
    sourceOfTruth: 'engine/hydroma/climate_adaptation/uncertainty_knowledge_engine.py',
    executionEndpoint: null,
  },

  // Carbon and MRV
  {
    id: 'carbon-calculator',
    domain: 'carbon',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/carbon/calculator.py',
    executionEndpoint: null,
  },
  {
    id: 'mrv-nojin',
    domain: 'carbon',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/mrv/nojin_mrv.py',
    executionEndpoint: null,
  },
  {
    id: 'mrv-metrics',
    domain: 'carbon',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/mrv/metrics.py',
    executionEndpoint: null,
  },
  {
    id: 'mrv-quality-assurance',
    domain: 'carbon',
    category: 'workflow',
    sourceOfTruth: 'engine/hydroma/mrv/qa.py',
    executionEndpoint: null,
  },
  {
    id: 'mrv-iot-ingest',
    domain: 'carbon',
    category: 'service',
    sourceOfTruth: 'engine/hydroma/mrv/iot_ingest.py',
    executionEndpoint: null,
  },

  // Crop
  {
    id: 'crop-water-requirement',
    domain: 'crop',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/calculations/crop_water_req_calc.py',
    executionEndpoint: null,
  },
  {
    id: 'ndvi-analysis',
    domain: 'crop',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/crop/ndvi_analysis.py',
    executionEndpoint: null,
  },

  // Simulation and hybrid modelling
  {
    id: 'swat-runner',
    domain: 'modeling',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/simulation/runners/swat_runner.py',
    executionEndpoint: null,
  },
  {
    id: 'aquacrop-runner',
    domain: 'modeling',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/simulation/runners/aquacrop_runner.py',
    executionEndpoint: null,
  },
  {
    id: 'rothc-runner',
    domain: 'modeling',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/simulation/runners/rothc_runner.py',
    executionEndpoint: null,
  },
  {
    id: 'modflow6',
    domain: 'modeling',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/models/expansion/modflow6.py',
    executionEndpoint: null,
  },
  {
    id: 'swat-plus',
    domain: 'modeling',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/models/expansion/swat_plus.py',
    executionEndpoint: null,
  },
  {
    id: 'physics-informed-network',
    domain: 'modeling',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/hybrid_ml/pinn.py',
    executionEndpoint: null,
  },
  {
    id: 'gaussian-process-surrogate',
    domain: 'modeling',
    category: 'model',
    sourceOfTruth: 'engine/hydroma/hybrid_ml/gp_surrogate.py',
    executionEndpoint: null,
  },

  // Decision support
  {
    id: 'what-if-engine',
    domain: 'decision',
    category: 'workflow',
    sourceOfTruth: 'engine/hydroma/scenarios/whatif_engine.py',
    executionEndpoint: null,
  },
  {
    id: 'monte-carlo-scenarios',
    domain: 'decision',
    category: 'workflow',
    sourceOfTruth: 'engine/hydroma/scenarios/monte_carlo.py',
    executionEndpoint: null,
  },
  {
    id: 'scenario-manager',
    domain: 'decision',
    category: 'service',
    sourceOfTruth: 'engine/hydroma/scenarios/scenario_manager.py',
    executionEndpoint: null,
  },
  {
    id: 'crop-scenarios',
    domain: 'decision',
    category: 'workflow',
    sourceOfTruth: 'engine/hydroma/scenarios/crop_scenarios.py',
    executionEndpoint: null,
  },
  {
    id: 'decision-support',
    domain: 'decision',
    category: 'service',
    sourceOfTruth: 'engine/hydroma/decision_support/dss.py',
    executionEndpoint: null,
  },
  {
    id: 'optimization-optimizer',
    domain: 'decision',
    category: 'algorithm',
    sourceOfTruth: 'engine/hydroma/optimization/optimizer.py',
    executionEndpoint: null,
  },
];

export const SCIENTIFIC_TOOL_IDS: readonly string[] = SCIENTIFIC_TOOLS.map((tool) => tool.id);

export function getScientificTool(id: string): ScientificToolDeclaration | undefined {
  return SCIENTIFIC_TOOLS.find((tool) => tool.id === id);
}

export function isDeclaredScientificTool(id: string): boolean {
  return getScientificTool(id) !== undefined;
}

/** Params for `generateStaticParams`; `dynamicParams` still accepts new ids. */
export function scientificToolParams(): { toolId: string }[] {
  return SCIENTIFIC_TOOL_IDS.map((toolId) => ({ toolId }));
}

/**
 * A tool may only be presented as executable when the live tool registry
 * declares an execution path for it.
 */
export function resolveExecutionCapability(
  declared: ScientificToolDeclaration | undefined,
  endpointPath: string | null | undefined,
): DomainCapabilityState {
  const endpoint = endpointPath?.trim();
  if (declared === undefined || endpoint === undefined || endpoint === '') {
    return 'unavailable';
  }
  return 'available';
}

/** Languages the USSD menu preview endpoint accepts. */
export const USSD_MENU_LANGUAGES = ['en', 'fa', 'ar'] as const;

export type UssdMenuLanguage = (typeof USSD_MENU_LANGUAGES)[number];

export function isUssdMenuLanguage(value: string): value is UssdMenuLanguage {
  return (USSD_MENU_LANGUAGES as readonly string[]).includes(value);
}
