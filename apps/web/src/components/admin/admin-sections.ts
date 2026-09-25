import type { GlobalRole } from '@/lib/auth/roles';

/**
 * Tier 0 admin console model — the single source of truth for the console.
 *
 * One model drives the side navigation, every page heading, the per-page data
 * contract table and the honest-state copy, so a page can never advertise a
 * capability the shell does not know about.
 *
 * A capability is only reportable as a data source when it has either
 *
 * 1. a real registered gateway endpoint, or
 * 2. a real file that ships with the application (design tokens, message
 *    catalogues, the route registry itself).
 *
 * Anything else keeps `endpoint: null` and `localSource: null`, carries a
 * locale-neutral `gap` reason, and is always rendered as unavailable. No page
 * may substitute a counter, a flag, an audit row or a job for a missing
 * contract.
 */
export interface AdminCapability {
  id: string;
  /** Existing `namespace.key` message key for the capability label. */
  labelKey: string;
  method: 'GET' | 'POST';
  /** Real registered gateway endpoint, or `null` while the contract is missing. */
  endpoint: string | null;
  /** Verifiable repository file backing the capability when no endpoint exists. */
  localSource: string | null;
  /** Locale-neutral reason recorded for a capability without a data source. */
  gap: string;
  /** Extra upstream role the gateway itself requires, if any. */
  requiredRoles?: readonly GlobalRole[];
}

export interface AdminSection {
  id: string;
  /** Path below `/{locale}/admin`; the empty string is the console index. */
  path: string;
  /** Existing `namespace.key` message key used as the nav and page heading. */
  labelKey: string;
  /** Existing `namespace.key` message key used as the page lead. */
  leadKey: string;
  /** Extra upstream role gate, applied in addition to the console gate. */
  roles: readonly GlobalRole[];
  capabilities: readonly AdminCapability[];
}

const ADMIN_ONLY: readonly GlobalRole[] = ['admin'];
const CONTENT_ROLES: readonly GlobalRole[] = ['admin', 'content_admin'];
const SECURITY_ROLES: readonly GlobalRole[] = ['admin', 'security_admin'];
const USER_ROLES: readonly GlobalRole[] = ['admin', 'user_admin'];

const MESSAGES_DIR = 'apps/web/messages/*.json';
export const REGISTRY_FILE = 'apps/web/src/lib/domains/registry.ts';
const TOKENS_JSON = 'apps/web/tokens/dtcg.json';
const TOKENS_CSS = 'apps/web/tokens/variables.css';
const GLOBALS_CSS = 'apps/web/src/app/globals.css';

export const ADMIN_SECTIONS = [
  {
    id: 'overview',
    path: '',
    labelKey: 'admin.sections.overview',
    leadKey: 'admin.leads.overview',
    roles: ADMIN_ONLY,
    capabilities: [
      {
        id: 'platform-health',
        labelKey: 'statusPage.service',
        method: 'GET',
        endpoint: '/api/v1/platform/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'platform-stats',
        labelKey: 'statusPage.landscapes',
        method: 'GET',
        endpoint: '/api/v1/platform/stats',
        localSource: null,
        gap: '',
      },
      {
        id: 'service-matrix',
        labelKey: 'admin.capabilities.serviceMatrix',
        method: 'GET',
        endpoint: '/api/v1/satellite/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'admin-overview',
        labelKey: 'admin.capabilities.adminOverview',
        method: 'GET',
        // /api/v1/admin/overview answers with hard-coded placeholder counters
        // upstream, so the console never reports its values.
        endpoint: null,
        localSource: null,
        gap: 'services/api_gateway/routers/admin_overview.py returns placeholder counters',
        requiredRoles: ADMIN_ONLY,
      },
      {
        id: 'admin-channel-health',
        labelKey: 'admin.capabilities.channelHealth',
        method: 'GET',
        // /api/v1/admin/overview/health returns a fixed "healthy" list with
        // invented latency values, so it is never read.
        endpoint: null,
        localSource: null,
        gap: 'services/api_gateway/routers/admin_overview.py returns a hard-coded channel list',
        requiredRoles: ADMIN_ONLY,
      },
    ],
  },
  {
    id: 'system-health',
    path: 'system/health',
    labelKey: 'admin.sections.systemHealth',
    leadKey: 'admin.leads.systemHealth',
    roles: ADMIN_ONLY,
    capabilities: [
      {
        id: 'platform-health',
        labelKey: 'statusPage.service',
        method: 'GET',
        endpoint: '/api/v1/platform/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'satellite-health',
        labelKey: 'platformOverview.itemScience',
        method: 'GET',
        endpoint: '/api/v1/satellite/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'voice-health',
        labelKey: 'public.channels.voice',
        method: 'GET',
        endpoint: '/api/v1/voice/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'ai-health',
        labelKey: 'ai.title',
        method: 'GET',
        endpoint: '/api/v1/ai/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'land-health',
        labelKey: 'statusPage.landscapes',
        method: 'GET',
        endpoint: '/api/v1/land/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'blockchain-health',
        labelKey: 'trust.title',
        method: 'GET',
        endpoint: '/api/v1/blockchain/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'automation-health',
        labelKey: 'common.next',
        method: 'GET',
        endpoint: '/api/v1/automation/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'ecowallet-health',
        labelKey: 'market.wallet.title',
        method: 'GET',
        endpoint: '/api/v1/ecowallet/health',
        localSource: null,
        gap: '',
      },
      {
        id: 'cpp-kernel-status',
        labelKey: 'statusPage.cpp',
        method: 'GET',
        endpoint: '/api/v1/models/cpp-status',
        localSource: null,
        gap: '',
      },
    ],
  },
  {
    id: 'jobs',
    path: 'jobs',
    labelKey: 'admin.sections.jobs',
    leadKey: 'admin.leads.jobs',
    roles: ADMIN_ONLY,
    capabilities: [
      {
        id: 'job-index',
        labelKey: 'admin.capabilities.jobIndex',
        method: 'GET',
        // No queue, worker or job contract is registered in the OpenAPI
        // document, so no job record may be listed.
        endpoint: null,
        localSource: null,
        gap: 'no queue or job endpoint is registered in openapi.json',
      },
      {
        id: 'job-automation-runs',
        labelKey: 'admin.capabilities.automationRuns',
        method: 'GET',
        // /api/v1/automation/agent-run is a single ad-hoc run, not an index.
        endpoint: null,
        localSource: null,
        gap: 'services/api_gateway/routers/automation.py exposes a single run, not an index',
      },
    ],
  },
  {
    id: 'localization',
    path: 'localization/translations',
    labelKey: 'admin.sections.localization',
    leadKey: 'admin.leads.localization',
    roles: ADMIN_ONLY,
    capabilities: [
      {
        id: 'message-catalogues',
        labelKey: 'admin.capabilities.messageCatalogues',
        method: 'GET',
        // The 14 catalogues are real files in this repository: coverage and
        // machine-translation state are read from disk, never assumed.
        endpoint: null,
        localSource: MESSAGES_DIR,
        gap: '',
      },
      {
        id: 'legal-locales',
        labelKey: 'admin.capabilities.legalLocales',
        method: 'GET',
        endpoint: '/api/v1/legal-texts/locales',
        localSource: null,
        gap: '',
      },
      {
        id: 'content-translations',
        labelKey: 'admin.capabilities.contentTranslations',
        method: 'GET',
        // Translations are only readable per content item; no index contract.
        endpoint: null,
        localSource: null,
        gap: 'services/api_gateway/routers/admin_content.py only exposes per-item translations',
        requiredRoles: CONTENT_ROLES,
      },
    ],
  },
  {
    id: 'feature-flags',
    path: 'feature-flags',
    labelKey: 'admin.sections.featureFlags',
    leadKey: 'admin.leads.featureFlags',
    roles: ADMIN_ONLY,
    capabilities: [
      {
        id: 'capability-matrix',
        labelKey: 'admin.capabilities.capabilityMatrix',
        method: 'GET',
        // The registered capability matrix is the real, reviewable flag index
        // available to the web layer today.
        endpoint: null,
        localSource: REGISTRY_FILE,
        gap: '',
      },
      {
        id: 'settings-index',
        labelKey: 'admin.capabilities.settingsIndex',
        method: 'GET',
        // /api/v1/admin/settings is an in-memory placeholder that resets on
        // restart; it is not a source of truth for any flag.
        endpoint: null,
        localSource: null,
        gap: 'services/api_gateway/routers/admin_settings.py serves an in-memory store',
        requiredRoles: ADMIN_ONLY,
      },
    ],
  },
  {
    id: 'security',
    path: 'security',
    labelKey: 'admin.sections.security',
    leadKey: 'admin.leads.security',
    roles: SECURITY_ROLES,
    capabilities: [
      {
        id: 'login-history',
        labelKey: 'admin.capabilities.loginHistory',
        method: 'GET',
        // The router queries a LoginHistory model that is not registered in
        // database/models.py, so it cannot answer.
        endpoint: null,
        localSource: null,
        gap: 'services/api_gateway/routers/admin_security.py queries an unregistered model',
        requiredRoles: SECURITY_ROLES,
      },
      {
        id: 'security-audit',
        labelKey: 'admin.capabilities.securityAudit',
        method: 'GET',
        // The audit summary mixes real counters with hard-coded countries and
        // hard-coded suspicious-activity rows.
        endpoint: null,
        localSource: null,
        gap: 'services/api_gateway/routers/admin_security.py returns hard-coded audit rows',
        requiredRoles: SECURITY_ROLES,
      },
    ],
  },
  {
    id: 'content',
    path: 'content',
    labelKey: 'admin.sections.content',
    leadKey: 'admin.leads.content',
    roles: CONTENT_ROLES,
    capabilities: [
      {
        id: 'content-index',
        labelKey: 'admin.capabilities.contentIndex',
        method: 'GET',
        endpoint: '/api/v1/admin/content',
        localSource: null,
        gap: '',
        requiredRoles: CONTENT_ROLES,
      },
      {
        id: 'content-writes',
        labelKey: 'admin.capabilities.contentWrites',
        method: 'POST',
        // Registered write contract. This workstream is read-only, so no
        // content write is ever issued from the console.
        endpoint: '/api/v1/admin/content',
        localSource: null,
        gap: '',
        requiredRoles: CONTENT_ROLES,
      },
    ],
  },
  {
    id: 'users',
    path: 'users',
    labelKey: 'admin.sections.users',
    leadKey: 'admin.leads.users',
    roles: USER_ROLES,
    capabilities: [
      {
        id: 'users-index',
        labelKey: 'admin.capabilities.usersIndex',
        method: 'GET',
        endpoint: '/api/v1/admin/users',
        localSource: null,
        gap: '',
        requiredRoles: USER_ROLES,
      },
      {
        id: 'user-bulk-actions',
        labelKey: 'admin.capabilities.userBulkActions',
        method: 'POST',
        // Registered write contract. This workstream is read-only, so no block
        // or unblock action is ever issued from the console.
        endpoint: '/api/v1/admin/users/bulk-action',
        localSource: null,
        gap: '',
        requiredRoles: USER_ROLES,
      },
    ],
  },
  {
    id: 'design-tokens',
    path: 'design-tokens',
    labelKey: 'admin.sections.designTokens',
    leadKey: 'admin.leads.designTokens',
    roles: ADMIN_ONLY,
    capabilities: [
      {
        id: 'dtcg-tokens',
        labelKey: 'admin.capabilities.dtcgTokens',
        method: 'GET',
        endpoint: null,
        localSource: TOKENS_JSON,
        gap: '',
      },
      {
        id: 'css-variables',
        labelKey: 'admin.capabilities.cssVariables',
        method: 'GET',
        endpoint: null,
        localSource: TOKENS_CSS,
        gap: '',
      },
      {
        id: 'runtime-tokens',
        labelKey: 'admin.capabilities.runtimeTokens',
        method: 'GET',
        endpoint: null,
        localSource: GLOBALS_CSS,
        gap: '',
      },
    ],
  },
] as const satisfies readonly AdminSection[];

export function adminSectionHref(locale: string, path: string): string {
  return path === '' ? `/${locale}/admin` : `/${locale}/admin/${path}`;
}

export type AdminSectionId = (typeof ADMIN_SECTIONS)[number]['id'];

/** Non-optional lookup for a statically known section id. */
export function getAdminSection(id: AdminSectionId): AdminSection {
  const section = ADMIN_SECTIONS.find((entry) => entry.id === id);
  if (!section) throw new Error(`admin section is not registered: ${id}`);
  return section;
}

export function findAdminSection(id: string): AdminSection | undefined {
  return ADMIN_SECTIONS.find((section) => section.id === id);
}

export function findAdminCapability(
  section: AdminSection,
  capabilityId: string,
): AdminCapability | undefined {
  return section.capabilities.find((capability) => capability.id === capabilityId);
}

/** A capability has a data source only when a contract or a real local file backs it. */
export function isAdminCapabilitySourced(capability: AdminCapability): boolean {
  return capability.endpoint !== null || capability.localSource !== null;
}

export function adminCapabilitySource(capability: AdminCapability): string | null {
  return capability.endpoint ?? capability.localSource;
}
