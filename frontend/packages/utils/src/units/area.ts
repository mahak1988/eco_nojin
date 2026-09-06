/**
 * Area conversions. Internal unit: hectares (ha) — matches SWAT+ and RothC conventions.
 */

export const AREA_UNITS = ['ha', 'm2', 'km2', 'acre'] as const;
export type AreaUnit = (typeof AREA_UNITS)[number];

const TO_HA: Record<AreaUnit, number> = {
  ha: 1,
  m2: 1e-4,
  km2: 100,
  acre: 0.40468564224,
};

export function convertArea(value: number, from: AreaUnit, to: AreaUnit): number {
  return (value * TO_HA[from]) / TO_HA[to];
}