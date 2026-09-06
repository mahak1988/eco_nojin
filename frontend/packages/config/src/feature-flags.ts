/**
 * Feature flags for staged rollouts.
 * Override per-deploy via env injection (see `featureFlagsFromEnv`).
 */

type Flags = {
  enableNewDashboardLayout: boolean;
  enableRealTimeSensors: boolean;
  enableAiAssistant: boolean;
  enableCarbonMRV: boolean;
  enableMarketplace: boolean;
};

const DEFAULTS: Flags = {
  enableNewDashboardLayout: true,
  enableRealTimeSensors: false,
  enableAiAssistant: true,
  enableCarbonMRV: true,
  enableMarketplace: false,
};

export const flags: Flags = DEFAULTS;

export function featureFlagsFromEnv(env: Record<string, unknown>): Flags {
  return {
    enableNewDashboardLayout: boolFrom(env['VITE_FF_NEW_LAYOUT'], DEFAULTS.enableNewDashboardLayout),
    enableRealTimeSensors: boolFrom(env['VITE_FF_REALTIME'], DEFAULTS.enableRealTimeSensors),
    enableAiAssistant: boolFrom(env['VITE_FF_AI'], DEFAULTS.enableAiAssistant),
    enableCarbonMRV: boolFrom(env['VITE_FF_CARBON'], DEFAULTS.enableCarbonMRV),
    enableMarketplace: boolFrom(env['VITE_FF_MARKETPLACE'], DEFAULTS.enableMarketplace),
  };
}

function boolFrom(v: unknown, fallback: boolean): boolean {
  if (v === undefined || v === null) return fallback;
  return String(v) === 'true';
}

export type FeatureFlag = keyof Flags;