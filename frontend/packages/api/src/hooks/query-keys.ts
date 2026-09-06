/**
 * Centralized query keys. Avoid string literals sprinkled across apps.
 */
export const queryKeys = {
  dashboard: () => ['dashboard'] as const,
  dashboardSnapshot: () => ['dashboard', 'snapshot'] as const,

  soil: {
    profile: (boundsKey: string) => ['soil', 'profile', boundsKey] as const,
    sample: (req: unknown) => ['soil', 'sample', req] as const,
  },

  water: {
    balance: (req: unknown) => ['water', 'balance', req] as const,
    infiltration: (boundsKey: string) => ['water', 'infiltration', boundsKey] as const,
  },

  carbon: {
    projects: () => ['carbon', 'projects'] as const,
    estimate: (req: unknown) => ['carbon', 'estimate', req] as const,
  },

  motors: {
    run: (motor: string, req: unknown) => ['motors', motor, req] as const,
    chain: (req: unknown) => ['motors', 'chain', req] as const,
  },

  satellite: {
    scenes: (boundsKey: string) => ['satellite', 'scenes', boundsKey] as const,
    series: (req: unknown) => ['satellite', 'series', req] as const,
  },

  farms: {
    list: () => ['farms'] as const,
    detail: (id: string) => ['farms', id] as const,
  },
} as const;