/**
 * PlacedOpsMarkers Component
 * ===========================
 * Renders 3D pins for placed engineering operations on terrain.
 *
 * Features:
 * - Pin sticks (cylinders) anchored to terrain surface
 * - Spherical heads with emissive highlight for selected
 * - HTML labels using drei's Html component
 * - Click to select operation
 *
 * @module features/hydroma/components/canvas/PlacedOpsMarkers
 */

import { Html } from '@react-three/drei';
import type { TerrainData, PlacedOp } from '../../types';
import { getTerrainYAtPoint } from '../../utils/worldToTerrainY';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface PlacedOpsMarkersProps {
  /** Array of placed operations */
  ops: PlacedOp[];
  /** Terrain data for Y position calculation */
  data: TerrainData;
  /** Currently selected operation ID */
  selectedId: string | null;
  /** Callback when operation is selected */
  onSelect: (id: string) => void;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function PlacedOpsMarkers({ ops, data, selectedId, onSelect }: PlacedOpsMarkersProps) {
  return (
    <group>
      {ops.map((op) => {
        const yPos = getTerrainYAtPoint(data, op.x, op.y, 0.5);
        const isSelected = selectedId === op.id;

        return (
          <group key={op.id} position={[op.x, yPos, op.y]}>
            {/* Pin stick */}
            <mesh position={[0, -0.2, 0]}>
              <cylinderGeometry args={[0.04, 0.04, 0.5, 8]} />
              <meshStandardMaterial color="#8b5cf6" />
            </mesh>

            {/* Pin head */}
            <mesh
              position={[0, 0.15, 0]}
              onClick={(e) => {
                e.stopPropagation();
                onSelect(op.id);
              }}
            >
              <sphereGeometry args={[0.22, 16, 16]} />
              <meshStandardMaterial
                color={isSelected ? '#fbbf24' : '#8b5cf6'}
                emissive={isSelected ? '#fbbf24' : '#8b5cf6'}
                emissiveIntensity={isSelected ? 0.8 : 0.4}
              />
            </mesh>

            {/* Label */}
            <Html
              position={[0, 0.6, 0]}
              center
              occlude={false}
              zIndexRange={[100, 0]}
              style={{ pointerEvents: 'none' }}
            >
              <div
                style={{
                  background: isSelected ? 'rgba(251, 191, 36, 0.95)' : 'rgba(139, 92, 246, 0.95)',
                  color: 'white',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  whiteSpace: 'nowrap',
                  fontWeight: 700,
                  border: '1px solid rgba(255,255,255,0.3)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                  userSelect: 'none',
                }}
              >
                📍 {op.label}
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}
