/**
 * Volume conversions. Internal unit: cubic meters (m³).
 */
export const VOLUME_UNITS = ['m3', 'L', 'ML', 'gal'] as const;
export type VolumeUnit = (typeof VOLUME_UNITS)[number];

const TO_M3: Record<VolumeUnit, number> = {
  m3: 1,
  L: 0.001,
  ML: 1000,
  gal: 0.003785411784,
};

export function convertVolume(value: number, from: VolumeUnit, to: VolumeUnit): number {
  return (value * TO_M3[from]) / TO_M3[to];
}