/**
 * Professional workspace contract — `docs/frontend/WORKSPACE_SECURITY_DESIGN.md`.
 *
 * THE REGISTRY IS DESCRIPTIVE ONLY. It documents which roles, pages and
 * backend capabilities the professional workspace knows about. It is never an
 * authorization authority: the gateway session is the only issuer of a role and
 * the only source of a record. A role listed here without `issuedByGateway`
 * cannot reach a professional page today, because the gateway does not mint it.
 *
 * Every visible string is an existing `namespace.key` message key. The shared
 * catalogues are owned outside this workstream, so no key is added here; the
 * missing `workspace.*` namespace is reported as a blocker instead.
 *
 * A capability is reportable as a data source only when it declares either
 *
 * 1. a real registered gateway endpoint, or
 * 2. a real same-origin BFF route that ships with the application.
 *
 * Anything else keeps `endpoint: null`, carries a locale-neutral `gap` reason and
 * is always rendered as unavailable. No page may substitute a counter, a flag, a
 * job, an audit row or a customer record for a missing contract.
 */

/** Management roles the platform gateway issues today. */
export const WORKSPACE_MANAGEMENT_ROLES = [
  'admin',
  'security_admin',
  'content_admin',
  'user_admin',
] as const;

/**
 * Professional roles the design document proposes. `advisor` already exists in
 * the gateway role constants; the remaining six are proposed only, so a user can
 * only hold them if the gateway starts issuing them.
 */
export const WORKSPACE_PROFESSIONAL_ROLES = [
  'advisor',
  'operator',
  'support',
  'analyst',
  'content_editor',
  'auditor',
  'manager',
] as const;

export type WorkspaceManagementRole = (typeof WORKSPACE_MANAGEMENT_ROLES)[number];
export type WorkspaceProfessionalRole = (typeof WORKSPACE_PROFESSIONAL_ROLES)[number];
export type WorkspaceRole = WorkspaceManagementRole | WorkspaceProfessionalRole;
export type WorkspaceRoleKind = 'management' | 'professional';

/** Consumer and platform roles the workspace never admits. */
export const WORKSPACE_DENIED_ROLES = [
  'regular',
  'tourist',
  'farmer',
  'researcher',
  'organization',
  'guest',
  '',
] as const;

/** The server-side workspace allowlist: management plus professional roles. */
export const WORKSPACE_ALLOWED_ROLES: readonly WorkspaceRole[] = [
  ...WORKSPACE_MANAGEMENT_ROLES,
  ...WORKSPACE_PROFESSIONAL_ROLES,
];

export interface WorkspaceRoleDescriptor {
  id: WorkspaceRole;
  kind: WorkspaceRoleKind;
  /**
   * True only when the gateway can actually mint this role. A false value means
   * the registry describes an intended role and the gateway issues none.
   */
  issuedByGateway: boolean;
  /** Existing translated label, or `null` when the catalogue has no key yet. */
  labelKey: string | null;
}

export const WORKSPACE_ROLE_DESCRIPTORS: readonly WorkspaceRoleDescriptor[] = [
  { id: 'admin', kind: 'management', issuedByGateway: true, labelKey: 'auth.roles.admin' },
  {
    id: 'security_admin',
    kind: 'management',
    issuedByGateway: true,
    labelKey: 'auth.roles.security_admin',
  },
  {
    id: 'content_admin',
    kind: 'management',
    issuedByGateway: true,
    labelKey: 'auth.roles.content_admin',
  },
  {
    id: 'user_admin',
    kind: 'management',
    issuedByGateway: true,
    labelKey: 'auth.roles.user_admin',
  },
  { id: 'advisor', kind: 'professional', issuedByGateway: true, labelKey: 'auth.roles.advisor' },
  {
    id: 'operator',
    kind: 'professional',
    issuedByGateway: false,
    labelKey: 'workspace.roles.operator',
  },
  {
    id: 'support',
    kind: 'professional',
    issuedByGateway: false,
    labelKey: 'workspace.roles.support',
  },
  {
    id: 'analyst',
    kind: 'professional',
    issuedByGateway: false,
    labelKey: 'workspace.roles.analyst',
  },
  {
    id: 'content_editor',
    kind: 'professional',
    issuedByGateway: false,
    labelKey: 'workspace.roles.content_editor',
  },
  {
    id: 'auditor',
    kind: 'professional',
    issuedByGateway: false,
    labelKey: 'workspace.roles.auditor',
  },
  {
    id: 'manager',
    kind: 'professional',
    issuedByGateway: false,
    labelKey: 'workspace.roles.manager',
  },
] as const;

export function isWorkspaceRole(role: string | null | undefined): role is WorkspaceRole {
  return typeof role === 'string' && WORKSPACE_ALLOWED_ROLES.includes(role as WorkspaceRole);
}

export function findWorkspaceRole(role: string): WorkspaceRoleDescriptor | undefined {
  return WORKSPACE_ROLE_DESCRIPTORS.find((descriptor) => descriptor.id === role);
}

/** Roles the gateway is able to issue today, regardless of the registry. */
export function gatewayIssuedRoles(): readonly WorkspaceRole[] {
  return WORKSPACE_ROLE_DESCRIPTORS.filter((descriptor) => descriptor.issuedByGateway).map(
    (descriptor) => descriptor.id,
  );
}

/** Describes a role without ever granting it. */
export function describeWorkspaceRole(role: string | null | undefined): {
  id: string;
  inAllowlist: boolean;
  issuedByGateway: boolean;
  labelKey: string | null;
} {
  const id = typeof role === 'string' ? role : '';
  const descriptor = findWorkspaceRole(id);
  return {
    id,
    inAllowlist: isWorkspaceRole(id),
    issuedByGateway: descriptor?.issuedByGateway === true,
    labelKey: descriptor?.labelKey ?? null,
  };
}

export type WorkspacePageId =
  | 'overview'
  | 'assignments'
  | 'cases'
  | 'knowledge'
  | 'reports'
  | 'team'
  | 'approvals'
  | 'targets'
  | 'audit'
  | 'operations'
  | 'operations-jobs'
  | 'operations-events'
  | 'operations-health'
  | 'settings'
  | 'settings-notifications'
  | 'settings-access';

export type WorkspaceGroupId = 'work' | 'governance' | 'operations' | 'settings';

export type WorkspaceEndpointKind = 'gateway' | 'bff';

export interface WorkspaceCapability {
  id: string;
  /** Existing `namespace.key` message key for the capability label. */
  labelKey: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** Real registered endpoint, or `null` while the contract is missing. */
  endpoint: string | null;
  /** Which server registers `endpoint`; a BFF route never leaves this origin. */
  endpointKind?: WorkspaceEndpointKind;
  /** Locale-neutral reason recorded for a capability without a data source. */
  gap: string;
  /**
   * Restricts the columns a payload may expose. `non-personal` is used where the
   * response carries personal data the backend declares no scope for.
   */
  projection?: 'non-personal';
  /**
   * Upstream role the gateway itself requires. `null` means the endpoint applies
   * no role gate at all, which the page must disclose instead of hide.
   */
  upstreamRoles?: readonly string[] | null;
}

export interface WorkspacePage {
  id: WorkspacePageId;
  groupId: WorkspaceGroupId;
  /** Path below `/{locale}/workspace`; the empty string is the workspace root. */
  path: string;
  /** Existing `namespace.key` message key used as the nav and page heading. */
  labelKey: string;
  /** Existing `namespace.key` message key used as the page lead. */
  leadKey: string;
  /**
   * Descriptive professional scope for this page. It filters the navigation and is
   * reported to the reader; it is not a second authorization gate.
   */
  roles: readonly WorkspaceRole[];
  capabilities: readonly WorkspaceCapability[];
}

const ALL_ROLES = WORKSPACE_ALLOWED_ROLES;
const OPERATIONS_ROLES: readonly WorkspaceRole[] = ['operator', 'manager', 'admin'];
const AUDIT_ROLES: readonly WorkspaceRole[] = ['auditor', 'security_admin', 'admin'];

/** The BFF session route is a real same-origin endpoint, not a file. */
export const WORKSPACE_SESSION_ENDPOINT = '/api/auth/session';
export const WORKSPACE_SESSION_ENDPOINT_KIND: WorkspaceEndpointKind = 'bff';

export const WORKSPACE_ORGANIZATIONS_ENDPOINT = '/api/v1/organizations';
export const WORKSPACE_LEGAL_TEXTS_ENDPOINT = '/api/v1/legal-texts?status=published&limit=50';
export const WORKSPACE_CONTENT_SEARCH_ENDPOINT = '/api/v1/content/search';
export const WORKSPACE_SECURITY_EVENTS_ENDPOINT = '/api/v1/security/events?limit=50';
export const WORKSPACE_SYNC_STATUS_ENDPOINT = '/api/v1/sync/status';
export const WORKSPACE_NOTIFICATION_ENDPOINT = '/api/v1/auth/notifications';
export const WORKSPACE_EXPORT_ENDPOINT = '/api/v1/auth/export-data';

const HEALTH_CAPABILITIES: readonly WorkspaceCapability[] = [
  {
    id: 'platform-health',
    labelKey: 'statusPage.service',
    method: 'GET',
    endpoint: '/api/v1/platform/health',
    gap: '',
  },
  {
    id: 'satellite-health',
    labelKey: 'platformOverview.itemScience',
    method: 'GET',
    endpoint: '/api/v1/satellite/health',
    gap: '',
  },
  {
    id: 'land-health',
    labelKey: 'statusLine.landProfiles',
    method: 'GET',
    endpoint: '/api/v1/land/health',
    gap: '',
  },
  {
    id: 'ai-health',
    labelKey: 'ai.title',
    method: 'GET',
    endpoint: '/api/v1/ai/health',
    gap: '',
  },
  {
    id: 'voice-health',
    labelKey: 'public.channels.voice',
    method: 'GET',
    endpoint: '/api/v1/voice/health',
    gap: '',
  },
  {
    id: 'blockchain-health',
    labelKey: 'trust.title',
    method: 'GET',
    endpoint: '/api/v1/blockchain/health',
    gap: '',
  },
  {
    id: 'automation-health',
    labelKey: 'admin.sections.jobs',
    method: 'GET',
    endpoint: '/api/v1/automation/health',
    gap: '',
  },
  {
    id: 'ecowallet-health',
    labelKey: 'market.wallet.title',
    method: 'GET',
    endpoint: '/api/v1/ecowallet/health',
    gap: '',
  },
  {
    id: 'security-status',
    labelKey: 'admin.sections.security',
    method: 'GET',
    endpoint: '/api/v1/security/status',
    gap: '',
  },
  {
    id: 'sync-status',
    labelKey: 'statusPage.supabase',
    method: 'GET',
    endpoint: WORKSPACE_SYNC_STATUS_ENDPOINT,
    gap: '',
  },
  {
    id: 'cpp-kernel-status',
    labelKey: 'statusPage.cpp',
    method: 'GET',
    endpoint: '/api/v1/models/cpp-status',
    gap: '',
  },
] as const;

export const WORKSPACE_PAGES: readonly WorkspacePage[] = [
  {
    id: 'overview',
    groupId: 'work',
    path: 'overview',
    labelKey: 'workspace.pages.overview',
    leadKey: 'workspace.leads.overview',
    roles: ALL_ROLES,
    capabilities: [
      {
        id: 'workspace-kpis',
        labelKey: 'statusPage.label',
        method: 'GET',
        endpoint: null,
        gap: 'the gateway registers no assignment, case, approval or KPI endpoint',
      },
      {
        id: 'session-context',
        labelKey: 'auth.session.title',
        method: 'GET',
        endpoint: WORKSPACE_SESSION_ENDPOINT,
        endpointKind: WORKSPACE_SESSION_ENDPOINT_KIND,
        gap: '',
      },
      {
        id: 'organization-context',
        labelKey: 'auth.roles.organization',
        method: 'GET',
        endpoint: WORKSPACE_ORGANIZATIONS_ENDPOINT,
        gap: '',
      },
    ],
  },
  {
    id: 'assignments',
    groupId: 'work',
    path: 'assignments',
    labelKey: 'workspace.pages.assignments',
    leadKey: 'workspace.leads.assignments',
    roles: ['advisor', 'operator', 'manager', 'admin'],
    capabilities: [
      {
        id: 'assignment-index',
        labelKey: 'common.pending',
        method: 'GET',
        endpoint: null,
        gap: 'no assignment, task or queue index is registered in the gateway',
      },
      {
        id: 'assignment-writes',
        labelKey: 'common.open',
        method: 'POST',
        endpoint: null,
        gap: 'no assignment write contract is registered; the workspace never issues one',
      },
    ],
  },
  {
    id: 'cases',
    groupId: 'work',
    path: 'cases',
    labelKey: 'workspace.pages.cases',
    leadKey: 'workspace.leads.cases',
    roles: ['advisor', 'operator', 'support', 'manager', 'admin'],
    capabilities: [
      {
        id: 'case-index',
        labelKey: 'common.card',
        method: 'GET',
        endpoint: null,
        gap: 'no case, ticket or dispute index is registered in the gateway',
      },
      {
        id: 'case-evidence',
        labelKey: 'common.evidence',
        method: 'GET',
        endpoint: null,
        gap: 'no per-case evidence contract is registered in the gateway',
      },
    ],
  },
  {
    id: 'knowledge',
    groupId: 'work',
    path: 'knowledge',
    labelKey: 'workspace.pages.knowledge',
    leadKey: 'workspace.leads.knowledge',
    roles: ALL_ROLES,
    capabilities: [
      {
        id: 'document-catalogue',
        labelKey: 'legal.title',
        method: 'GET',
        endpoint: WORKSPACE_LEGAL_TEXTS_ENDPOINT,
        gap: '',
      },
      {
        id: 'content-search',
        labelKey: 'public.science.evidenceBase.evidenceCatalog',
        method: 'GET',
        endpoint: WORKSPACE_CONTENT_SEARCH_ENDPOINT,
        gap: '',
      },
      {
        id: 'knowledge-writes',
        labelKey: 'admin.sections.content',
        method: 'POST',
        endpoint: null,
        gap: 'the only knowledge write contract is the admin legal-text router, which this surface never calls',
      },
    ],
  },
  {
    id: 'reports',
    groupId: 'work',
    path: 'reports',
    labelKey: 'workspace.pages.reports',
    leadKey: 'workspace.leads.reports',
    roles: ['analyst', 'auditor', 'manager', 'admin'],
    capabilities: [
      {
        id: 'report-index',
        labelKey: 'statusPage.result',
        method: 'GET',
        endpoint: null,
        gap: 'the gateway registers no professional report index',
      },
      {
        id: 'report-schedule',
        labelKey: 'common.next',
        method: 'POST',
        endpoint: null,
        gap: 'no report scheduling contract is registered in the gateway',
      },
      {
        id: 'report-export',
        labelKey: 'common.view',
        method: 'POST',
        // The endpoint exists but answers with a placeholder download URL and is
        // not role-gated, so an export may never be offered from this surface.
        endpoint: null,
        gap: 'POST /api/v1/auth/export-data answers with a placeholder download URL and applies no role gate',
      },
    ],
  },
  {
    id: 'team',
    groupId: 'governance',
    path: 'team',
    labelKey: 'workspace.pages.team',
    leadKey: 'workspace.leads.team',
    roles: ['manager', 'admin', 'user_admin'],
    capabilities: [
      {
        id: 'organization-index',
        labelKey: 'auth.roles.organization',
        method: 'GET',
        endpoint: WORKSPACE_ORGANIZATIONS_ENDPOINT,
        gap: '',
      },
      {
        id: 'member-index',
        labelKey: 'statusLine.beneficiaries',
        method: 'GET',
        endpoint: null,
        gap: 'no member list endpoint is registered; the invite route writes a placeholder member id',
      },
      {
        id: 'member-invites',
        labelKey: 'common.open',
        method: 'POST',
        endpoint: null,
        gap: 'POST /api/v1/organizations/{org_id}/members stores a generated placeholder member id',
      },
    ],
  },
  {
    id: 'approvals',
    groupId: 'governance',
    path: 'approvals',
    labelKey: 'workspace.pages.approvals',
    leadKey: 'workspace.leads.approvals',
    roles: ['manager', 'content_admin', 'admin'],
    capabilities: [
      {
        id: 'approval-index',
        labelKey: 'market.bazaar.pending',
        method: 'GET',
        endpoint: null,
        gap: 'the gateway registers no approval index for professional work',
      },
      {
        id: 'approval-actions',
        labelKey: 'common.open',
        method: 'POST',
        endpoint: null,
        gap: 'approval actions exist only as POST routes over personal data with no declared scope',
      },
    ],
  },
  {
    id: 'targets',
    groupId: 'governance',
    path: 'targets',
    labelKey: 'workspace.pages.targets',
    leadKey: 'workspace.leads.targets',
    roles: ['analyst', 'manager', 'admin'],
    capabilities: [
      {
        id: 'target-index',
        labelKey: 'statusPage.label',
        method: 'GET',
        endpoint: null,
        gap: 'the gateway registers no target, goal or objective index',
      },
      {
        id: 'target-measurement',
        labelKey: 'statusPage.result',
        method: 'GET',
        endpoint: null,
        gap: 'no target measurement contract is registered in the gateway',
      },
    ],
  },
  {
    id: 'audit',
    groupId: 'governance',
    path: 'audit',
    labelKey: 'workspace.pages.audit',
    leadKey: 'workspace.leads.audit',
    roles: AUDIT_ROLES,
    capabilities: [
      {
        id: 'audit-events',
        labelKey: 'common.evidence',
        method: 'GET',
        endpoint: WORKSPACE_SECURITY_EVENTS_ENDPOINT,
        // The upstream route applies no role gate and declares no scope for the
        // personal fields it carries, so only the non-personal projection shows.
        projection: 'non-personal',
        upstreamRoles: null,
        gap: '',
      },
      {
        id: 'audit-access-log',
        labelKey: 'auth.session.title',
        method: 'GET',
        endpoint: null,
        gap: 'the admin security router answers with hard-coded audit rows',
      },
      {
        id: 'audit-export',
        labelKey: 'common.view',
        method: 'POST',
        endpoint: null,
        gap: 'no role-gated audit export contract is registered in the gateway',
      },
    ],
  },
  {
    id: 'operations',
    groupId: 'operations',
    path: 'operations',
    labelKey: 'workspace.pages.operations',
    leadKey: 'workspace.leads.operations',
    roles: OPERATIONS_ROLES,
    capabilities: [
      {
        id: 'operations-sync',
        labelKey: 'statusPage.supabase',
        method: 'GET',
        endpoint: WORKSPACE_SYNC_STATUS_ENDPOINT,
        gap: '',
      },
      {
        id: 'operations-jobs',
        labelKey: 'admin.sections.jobs',
        method: 'GET',
        endpoint: null,
        gap: 'no queue or job index is registered in the gateway',
      },
      {
        id: 'operations-events',
        labelKey: 'market.escrow.eventTimeline',
        method: 'GET',
        endpoint: WORKSPACE_SECURITY_EVENTS_ENDPOINT,
        projection: 'non-personal',
        upstreamRoles: null,
        gap: '',
      },
    ],
  },
  {
    id: 'operations-jobs',
    groupId: 'operations',
    path: 'operations/jobs',
    labelKey: 'workspace.pages.operationsJobs',
    leadKey: 'workspace.leads.operationsJobs',
    roles: OPERATIONS_ROLES,
    capabilities: [
      {
        id: 'job-index',
        labelKey: 'admin.sections.jobs',
        method: 'GET',
        endpoint: null,
        gap: 'no queue, worker or job contract is registered in the gateway',
      },
      {
        id: 'job-automation-runs',
        labelKey: 'statusPage.result',
        method: 'GET',
        endpoint: null,
        gap: 'the automation router exposes a single ad-hoc run, not an index',
      },
    ],
  },
  {
    id: 'operations-events',
    groupId: 'operations',
    path: 'operations/events',
    labelKey: 'workspace.pages.operationsEvents',
    leadKey: 'workspace.leads.operationsEvents',
    roles: ['operator', 'auditor', 'manager', 'security_admin', 'admin'],
    capabilities: [
      {
        id: 'security-events',
        labelKey: 'market.escrow.eventTimeline',
        method: 'GET',
        endpoint: WORKSPACE_SECURITY_EVENTS_ENDPOINT,
        projection: 'non-personal',
        upstreamRoles: null,
        gap: '',
      },
      {
        id: 'bridge-events',
        labelKey: 'statusPage.rows',
        method: 'GET',
        endpoint: null,
        gap: 'the bridge events route is scoped to one credit identifier, not an index',
      },
    ],
  },
  {
    id: 'operations-health',
    groupId: 'operations',
    path: 'operations/health',
    labelKey: 'workspace.pages.operationsHealth',
    leadKey: 'workspace.leads.operationsHealth',
    roles: ['operator', 'auditor', 'manager', 'security_admin', 'admin'],
    capabilities: HEALTH_CAPABILITIES,
  },
  {
    id: 'settings',
    groupId: 'settings',
    path: 'settings',
    labelKey: 'workspace.pages.settings',
    leadKey: 'workspace.leads.settings',
    roles: ALL_ROLES,
    capabilities: [
      {
        id: 'settings-index',
        labelKey: 'admin.capabilities.settingsIndex',
        method: 'GET',
        endpoint: null,
        gap: 'the admin settings router serves an in-memory map that resets on restart',
      },
      {
        id: 'settings-preferences',
        labelKey: 'auth.session.language',
        method: 'GET',
        endpoint: null,
        gap: 'the preferences router answers with a fixed payload for every field but language',
      },
    ],
  },
  {
    id: 'settings-notifications',
    groupId: 'settings',
    path: 'settings/notifications',
    labelKey: 'workspace.pages.settingsNotifications',
    leadKey: 'workspace.leads.settingsNotifications',
    roles: ALL_ROLES,
    capabilities: [
      {
        id: 'notification-preferences',
        labelKey: 'admin.capabilities.messageCatalogues',
        method: 'GET',
        // Registered, but the payload is a literal in the router rather than a
        // stored preference, so no preference may be shown as saved.
        endpoint: null,
        gap: 'GET /api/v1/auth/notifications answers with a fixed payload that no store backs',
      },
      {
        id: 'notification-delivery',
        labelKey: 'common.live',
        method: 'PUT',
        endpoint: null,
        gap: 'the notification update route answers success without persisting anything',
      },
    ],
  },
  {
    id: 'settings-access',
    groupId: 'settings',
    path: 'settings/access',
    labelKey: 'workspace.pages.settingsAccess',
    leadKey: 'workspace.leads.settingsAccess',
    roles: ['manager', 'security_admin', 'user_admin', 'admin'],
    capabilities: [
      {
        id: 'session-role',
        labelKey: 'auth.session.role',
        method: 'GET',
        endpoint: WORKSPACE_SESSION_ENDPOINT,
        endpointKind: WORKSPACE_SESSION_ENDPOINT_KIND,
        gap: '',
      },
      {
        id: 'membership-roles',
        labelKey: 'auth.roles.organization',
        method: 'GET',
        endpoint: WORKSPACE_ORGANIZATIONS_ENDPOINT,
        gap: '',
      },
      {
        id: 'mfa-state',
        labelKey: 'auth.session.emailVerified',
        method: 'GET',
        endpoint: null,
        gap: 'the gateway MFA dependency reads a field the user model does not define; no MFA contract is registered',
      },
      {
        id: 'role-assignment',
        labelKey: 'admin.sections.users',
        method: 'POST',
        endpoint: null,
        gap: 'no role-assignment endpoint is registered; the register route accepts a role from the client',
      },
    ],
  },
] as const satisfies readonly WorkspacePage[];

export interface WorkspaceNavigationGroup {
  id: WorkspaceGroupId;
  pages: readonly WorkspacePage[];
}

const GROUP_ORDER: readonly WorkspaceGroupId[] = ['work', 'governance', 'operations', 'settings'];

const GROUP_PAGE_IDS: Record<WorkspaceGroupId, readonly WorkspacePageId[]> = {
  work: ['overview', 'assignments', 'cases', 'knowledge', 'reports'],
  governance: ['team', 'approvals', 'targets', 'audit'],
  operations: ['operations', 'operations-jobs', 'operations-events', 'operations-health'],
  settings: ['settings', 'settings-notifications', 'settings-access'],
};

export const WORKSPACE_PAGE_IDS: readonly WorkspacePageId[] = WORKSPACE_PAGES.map(
  (page) => page.id,
);

/** Groups in navigation order, with no empty group and no duplicate page. */
export function workspaceNavigationGroups(): readonly WorkspaceNavigationGroup[] {
  return GROUP_ORDER.map((id) => ({
    id,
    pages: GROUP_PAGE_IDS[id]
      .map((pageId) => getWorkspacePage(pageId))
      .filter((page): page is WorkspacePage => page !== undefined),
  })).filter((group) => group.pages.length > 0);
}

export function workspacePageHref(locale: string, path: string): string {
  return path === '' ? `/${locale}/workspace` : `/${locale}/workspace/${path}`;
}

/** Non-optional lookup for a statically known page id. */
export function getWorkspacePage(id: WorkspacePageId): WorkspacePage {
  const page = WORKSPACE_PAGES.find((entry) => entry.id === id);
  if (!page) throw new Error(`workspace page is not registered: ${id}`);
  return page;
}

export function findWorkspacePage(id: string): WorkspacePage | undefined {
  return WORKSPACE_PAGES.find((page) => page.id === id);
}

export function findWorkspacePageByPath(path: string): WorkspacePage | undefined {
  return WORKSPACE_PAGES.find((page) => page.path === path);
}

export function findWorkspaceCapability(
  page: WorkspacePage,
  capabilityId: string,
): WorkspaceCapability | undefined {
  return page.capabilities.find((capability) => capability.id === capabilityId);
}

export function isWorkspaceCapabilitySourced(capability: WorkspaceCapability): boolean {
  return capability.endpoint !== null;
}

export function workspaceCapabilitySource(capability: WorkspaceCapability): string | null {
  return capability.endpoint;
}

/** Only a registered endpoint that answered may be reported as available. */
export function resolveCapabilityState(
  capability: WorkspaceCapability,
  ok: boolean,
): 'available' | 'unavailable' {
  return isWorkspaceCapabilitySourced(capability) && ok ? 'available' : 'unavailable';
}

export function workspaceCapabilityEndpoints(
  page: WorkspacePage,
  kind?: WorkspaceEndpointKind,
): readonly WorkspaceCapability[] {
  const sourced = page.capabilities.filter(
    (capability): capability is WorkspaceCapability & { endpoint: string } =>
      capability.endpoint !== null,
  );
  return kind === undefined ? sourced : sourced.filter((item) => item.endpointKind === kind);
}

/** Navigation entries for a role. Filtering hides links; it never grants access. */
export function workspacePagesForRole(role: string | null | undefined): readonly WorkspacePage[] {
  if (!isWorkspaceRole(role)) return [];
  return WORKSPACE_PAGES.filter((page) => page.roles.includes(role));
}

export function workspaceNavigationForRole(
  role: string | null | undefined,
): readonly WorkspaceNavigationGroup[] {
  const allowed = new Set(workspacePagesForRole(role).map((page) => page.id));
  return workspaceNavigationGroups()
    .map((group) => ({
      id: group.id,
      pages: group.pages.filter((page) => allowed.has(page.id)),
    }))
    .filter((group) => group.pages.length > 0);
}

/** Whether a page's descriptive scope includes the session role. */
export function isPageInRoleScope(page: WorkspacePage, role: string | null | undefined): boolean {
  return isWorkspaceRole(role) && page.roles.includes(role);
}
