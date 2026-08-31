/**
 * WindArrows Component
 * =====================
 * Visualizes wind direction and speed as arrows floating above terrain.
 *
 * Features:
 * - Arrow grid (4x4) positioned on terrain surface
 * - Arrow length proportional to wind speed
 * - Arrow rotation based on wind direction
 * - Auto-hidden when wind speed < 5 km/h
 * - Emissive purple material for visual appeal
 *
 * @module features/hydroma/components/canvas/WindArrows
 */

import { useMemo } from 'react';
import type { TerrainData } from '../../types';
import { getTerrainYAtPoint } from '../../utils/worldToTerrainY';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface WindArrowsProps {
  /** Terrain data for Y positioning */
  data: TerrainData;
  /** Wind direction in degrees (0-360, 0=North) */
  direction: number;
  /** Wind speed in km/h */
  speed: number;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function WindArrows({ data, direction, speed }: WindArrowsProps) {
  // Generate arrow positions on a 4x4 grid
  const arrows = useMemo(() => {
    if (speed < 5) return [];

    const result: Array<{ x: number; y: number; z: number }> = [];
    const grid = 4;

    for (let i = 0; i < grid; i++) {
      for (let j = 0; j < grid; j++) {
        const x = -7.5 + i * 5;
        const z = -7.5 + j * 5;
        const y = getTerrainYAtPoint(data, x, z, 0.4);
        result.push({ x, y, z });
      }
    }

    return result;
  }, [data, speed]);

  if (arrows.length === 0) return null;

  // Arrow length scales with wind speed (max 2 units)
  const len = Math.min(2, speed / 25);
  // Convert compass direction to 3D rotation
  const angle = ((direction - 90) * Math.PI) / 180;

  return (
    <group>
      {arrows.map((a, i) => (
        <group key={i} position={[a.x, a.y, a.z]} rotation={[0, angle, 0]}>
          {/* Arrow shaft (cylinder) */}
          <mesh position={[0, 0, len / 2]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.04, 0.04, len, 6]} />
            <meshStandardMaterial color="#a855f7" emissive="#a855f7" emissiveIntensity={0.3} />
          </mesh>

          {/* Arrow head (cone) */}
          <mesh position={[0, 0, len]} rotation={[Math.PI / 2, 0, 0]}>
            <coneGeometry args={[0.12, 0.3, 8]} />
            <meshStandardMaterial color="#a855f7" emissive="#a855f7" emissiveIntensity={0.3} />
          </mesh>
        </group>
      ))}
    </group>
  );
}
