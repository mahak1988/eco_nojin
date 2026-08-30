/**
 * PolygonOverlay Component
 * =========================
 * Renders user-drawn polygons on terrain surface.
 *
 * Features:
 * - Closed polygon outlines using drei Line
 * - Vertex markers (spheres) at each point
 * - Centroid labels with area information
 * - Live preview of current drawing (dashed line)
 *
 * @module features/hydroma/components/canvas/PolygonOverlay
 */

import { Line, Html } from '@react-three/drei';
import * as THREE from 'three';
import type { TerrainData, Polygon } from '../../types';
import { getTerrainYAtPoint } from '../../utils/worldToTerrainY';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface PolygonOverlayProps {
  /** Array of completed polygons */
  polygons: Polygon[];
  /** Terrain data for Y position calculation */
  data: TerrainData;
  /** Points of currently drawing polygon */
  currentDrawing: Array<{ x: number; y: number }>;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function PolygonOverlay({
  polygons,
  data,
  currentDrawing,
}: PolygonOverlayProps) {
  /**
   * Convert 2D world point to 3D terrain position
   */
  const getPoint3D = (p: { x: number; y: number }): THREE.Vector3 => {
    return new THREE.Vector3(
      p.x,
      getTerrainYAtPoint(data, p.x, p.y, 0.15),
      p.y
    );
  };

  return (
    <group>
      {/* Rendered polygons */}
      {polygons.map((poly) => {
        if (poly.points.length < 3) return null;

        const linePoints = poly.points.map(getPoint3D);
        linePoints.push(linePoints[0]); // close polygon

        const centroid = {
          x: poly.points.reduce((s, p) => s + p.x, 0) / poly.points.length,
          y: poly.points.reduce((s, p) => s + p.y, 0) / poly.points.length,
        };

        return (
          <group key={poly.id}>
            {/* Polygon outline */}
            <Line points={linePoints} color={poly.color} lineWidth={3} />

            {/* Vertex markers */}
            {poly.points.map((p, i) => {
              const pos = getPoint3D(p);
              return (
                <mesh key={i} position={pos}>
                  <sphereGeometry args={[0.12, 16, 16]} />
                  <meshStandardMaterial
                    color={poly.color}
                    emissive={poly.color}
                    emissiveIntensity={0.6}
                  />
                </mesh>
              );
            })}

            {/* Centroid label */}
            <Html
              position={[centroid.x, 5, centroid.y]}
              center
              occlude={false}
              zIndexRange={[100, 0]}
              style={{ pointerEvents: 'none' }}
            >
              <div
                style={{
                  background: `${poly.color}dd`,
                  color: 'white',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  whiteSpace: 'nowrap',
                  fontWeight: 700,
                }}
              >
                📐 {poly.name}{' '}
                {poly.area ? `(${poly.area.toFixed(0)}m²)` : ''}
              </div>
            </Html>
          </group>
        );
      })}

      {/* Live preview of current drawing */}
      {currentDrawing.length > 0 && (
        <group>
          {/* Drawing points */}
          {currentDrawing.map((p, i) => {
            const pos = getPoint3D(p);
            return (
              <mesh key={i} position={pos}>
                <sphereGeometry args={[0.16, 16, 16]} />
                <meshStandardMaterial
                  color="#fbbf24"
                  emissive="#fbbf24"
                  emissiveIntensity={0.8}
                />
              </mesh>
            );
          })}

          {/* Dashed line preview */}
          {currentDrawing.length >= 2 && (
            <Line
              points={currentDrawing.map(getPoint3D)}
              color="#fbbf24"
              lineWidth={3}
              dashed
              dashScale={3}
            />
          )}
        </group>
      )}
    </group>
  );
}
