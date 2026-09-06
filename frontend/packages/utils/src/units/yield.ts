/**
 * Crop yield conversions. Internal unit: tonnes per hectare (t/ha).
 */
export const YIELD_UNITS = ['t_ha', 'kg_ha', 'lb_ac', 'bu_ac'] as const;
export type YieldUnit = (typeof YIELD_UNITS)[number];

const TO_T_HA: Record<YieldUnit, number> = {
  t_ha: 1,
  kg_ha: 0.001,
  lb_ac: 0.0011208511,
  bu_ac: 0.0672510737, // generic; bushel weight depends on crop
};

export function convertYield(value: number, from: YieldUnit, to: YieldUnit): number {
  return (value * TO_T_HA[from]) / TO_T_HA[to];
}