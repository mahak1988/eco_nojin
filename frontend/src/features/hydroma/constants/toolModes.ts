/**
 * Tool Modes
 * ==========
 * User interaction modes for terrain manipulation.
 *
 * @module features/hydroma/constants
 */

import type { ToolModeDef } from '../types';

/**
 * Available tool modes
 */
export const TOOL_MODES: ToolModeDef[] = [
  {
    id: 'orbit',
    label: 'Orbit',
    fa: 'چرخش',
    icon: '🖱️',
    color: '#10b981',
  },
  {
    id: 'draw-polygon',
    label: 'Draw Area',
    fa: 'ترسیم',
    icon: '📐',
    color: '#f59e0b',
  },
  {
    id: 'place-op',
    label: 'Place Op',
    fa: 'جانمایی',
    icon: '📍',
    color: '#8b5cf6',
  },
  {
    id: 'data-plot',
    label: 'Data Plot',
    fa: 'پلات داده',
    icon: '📊',
    color: '#39ff5a',
  },
] as const;
