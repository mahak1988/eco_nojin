/**
 * Length conversions. Internal unit: meters.
 */

export const LENGTH_UNITS = ['m', 'km', 'cm', 'mm', 'mi', 'ft'] as const;
export type LengthUnit = (typeof LENGTH_UNITS)[number];

const TO_METERS: Record<LengthUnit, number> = {
  m: 1,
  km: 1000,
  cm: 0.01,
  mm: 0.001,
  mi: 1609.344,
  ft: 0.3048,
};

export function convertLength(value: number, from: LengthUnit, to: LengthUnit): number {
  return (value * TO_METERS[from]) / TO_METERS[to];
}