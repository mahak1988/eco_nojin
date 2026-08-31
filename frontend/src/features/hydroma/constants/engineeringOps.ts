/**
 * Engineering Operations
 * ======================
 * Available engineering interventions for erosion control and water management.
 *
 * Each operation has:
 * - Unique identifier
 * - English and Persian names
 * - Emoji for quick visual identification
 * - Estimated cost (USD)
 *
 * @module features/hydroma/constants
 */

import type { EngineeringOp } from '../types';

/**
 * List of available engineering operations
 */
export const ENGINEERING_OPS: EngineeringOp[] = [
  {
    id: 'gabion',
    name: 'Gabion Wall',
    fa: 'دیوار گابیونی',
    emoji: '🧱',
    cost: 500,
  },
  {
    id: 'checkdam',
    name: 'Check Dam',
    fa: 'سد اصلاحی',
    emoji: '🚧',
    cost: 800,
  },
  {
    id: 'terrace',
    name: 'Terrace',
    fa: 'تراس',
    emoji: '🏞️',
    cost: 1200,
  },
  {
    id: 'spillway',
    name: 'Spillway',
    fa: 'سرریز',
    emoji: '🌊',
    cost: 2000,
  },
  {
    id: 'well',
    name: 'Well',
    fa: 'چاه',
    emoji: '🕳️',
    cost: 5000,
  },
  {
    id: 'pond',
    name: 'Pond',
    fa: 'حوضچه',
    emoji: '💧',
    cost: 3000,
  },
] as const;

/**
 * Get operation by ID
 */
export const getEngineeringOp = (id: string): EngineeringOp | undefined =>
  ENGINEERING_OPS.find((op) => op.id === id);

/**
 * Operations that reduce erosion (trigger RUSLE calculation)
 */
export const EROSION_REDUCING_OPS = ['terrace', 'checkdam', 'gabion'] as const;

/**
 * Check if operation reduces erosion
 */
export const isErosionReducingOp = (opId: string): boolean =>
  (EROSION_REDUCING_OPS as readonly string[]).includes(opId);
