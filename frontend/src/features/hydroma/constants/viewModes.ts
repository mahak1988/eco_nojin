/**
 * View Modes
 * ==========
 * Camera view presets for terrain visualization.
 *
 * @module features/hydroma/constants
 */

import type { ViewModeDef } from '../types';

/**
 * Available view modes
 */
export const VIEW_MODES: ViewModeDef[] = [
  { id: '3d', label: '3D', fa: '۳بُعدی' },
  { id: '2d-top', label: 'Top', fa: 'بالا' },
  { id: '2d-side', label: 'Side', fa: 'کنار' },
  { id: 'cross-section', label: 'Section', fa: 'برش' },
] as const;

/**
 * Camera positions for each view mode
 */
export const VIEW_MODE_POSITIONS: Record<string, { pos: [number, number, number]; lookAt: [number, number, number] }> = {
  '3d': { pos: [25, 22, 25], lookAt: [0, 0, 0] },
  '2d-top': { pos: [0, 30, 0.1], lookAt: [0, 0, 0] },
  '2d-side': { pos: [25, 4, 0], lookAt: [0, 0, 0] },
  'cross-section': { pos: [0, 5, 25], lookAt: [0, 0, 0] },
};
