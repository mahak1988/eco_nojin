/**
 * TerrainMesh Component
 * =====================
 * Renders 3D terrain using PlaneGeometry with vertex colors.
 *
 * Responsibilities:
 * - Create plane geometry from TerrainData
 * - Apply vertex colors based on layer type
 * - Handle click events on terrain
 * - Support texture overlay (Esri imagery)
 *
 * Supported layers:
 * - surface: Natural terrain with elevation-based coloring
 * - soil: Brown soil layer
 * - bedrock: Gray bedrock layer
 * - ndvi: Vegetation index (green gradient)
 * - moisture: Soil moisture (blue gradient)
 * - roots: Root depth visualization
 * - groundwater: Groundwater level
 *
 * @module features/hydroma/components/canvas/TerrainMesh
 */

import { useMemo, useCallback } from 'react';
import * as THREE from 'three';
import type { ThreeEvent } from '@react-three/fiber';
import type { TerrainData, LayerType } from '../../types';
import {
  WORLD_SIZE,
  HEIGHT_SCALE,
  terrainColor,
  moistureColor,
  rootColor,
  groundwaterColor,
} from '../../../../lib/terrainGenerator';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface TerrainMeshProps {
  /** Terrain data with elevation, moisture, etc. */
  data: TerrainData;
  /** Click handler for terrain interaction */
  onTerrainClick?: (point: THREE.Vector3, normal: THREE.Vector3) => void;
  /** Visibility toggle */
  visible?: boolean;
  /** Opacity (0-1) */
  opacity?: number;
  /** Layer type for coloring */
  layer?: LayerType;
  /** Optional texture overlay (e.g., Esri imagery) */
  map?: THREE.Texture | null;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function TerrainMesh({
  data,
  onTerrainClick,
  visible = true,
  opacity = 1,
  layer = 'surface',
  map = null,
}: TerrainMeshProps) {
  // ── Create base geometry (memoized by dimensions) ───────────────
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(WORLD_SIZE, WORLD_SIZE, data.width - 1, data.height - 1);
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, [data.width, data.height]);

  // ── Apply vertex positions and colors ───────────────────────────
  useMemo(() => {
    const positions = geometry.attributes.position;
    const colors = new Float32Array(positions.count * 3);
    const range = data.maxElevation - data.minElevation || 1;

    for (let i = 0; i < positions.count; i++) {
      const x = i % data.width;
      const y = Math.floor(i / data.width);

      if (y >= data.height || x >= data.width) continue;

      const elev = data.elevation[y][x];
      const norm = (elev - data.minElevation) / range;

      let r = 0,
        g = 0,
        b = 0,
        yOff = 0;

      switch (layer) {
        case 'surface': {
          [r, g, b] = terrainColor(data, x, y, norm);
          yOff = norm * HEIGHT_SCALE;
          break;
        }
        case 'soil': {
          r = 0.55;
          g = 0.4;
          b = 0.25;
          yOff = norm * HEIGHT_SCALE - 0.3;
          break;
        }
        case 'bedrock': {
          r = 0.45;
          g = 0.4;
          b = 0.4;
          yOff = norm * HEIGHT_SCALE - 0.8;
          break;
        }
        case 'ndvi': {
          const gv = 0.2 + 0.6 * data.moisture[y][x];
          r = 0.12;
          g = gv;
          b = 0.18;
          yOff = norm * HEIGHT_SCALE + 0.04;
          break;
        }
        case 'moisture': {
          [r, g, b] = moistureColor(data.moisture[y]?.[x] ?? 0);
          yOff = norm * HEIGHT_SCALE + 0.02;
          break;
        }
        case 'roots': {
          const depth = data.rootDepth?.[y]?.[x] ?? 0;
          [r, g, b] = rootColor(depth, 100);
          yOff = norm * HEIGHT_SCALE - (depth / 100) * 1.5;
          break;
        }
        case 'groundwater': {
          const gw = data.groundwater?.[y]?.[x] ?? 10;
          [r, g, b] = groundwaterColor(gw);
          yOff = norm * HEIGHT_SCALE - Math.min(3, gw / 10);
          break;
        }
      }

      positions.setY(i, yOff);
      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }

    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.computeVertexNormals();
  }, [data, layer, geometry]);

  // ── Click handler ───────────────────────────────────────────────
  const handleClick = useCallback(
    (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      if (onTerrainClick && e.point) {
        onTerrainClick(e.point, e.face?.normal || new THREE.Vector3(0, 1, 0));
      }
    },
    [onTerrainClick]
  );

  return (
    <mesh geometry={geometry} receiveShadow castShadow onClick={handleClick} visible={visible}>
      <meshStandardMaterial
        map={map || undefined}
        vertexColors
        roughness={0.85}
        metalness={0.05}
        transparent={opacity < 1}
        opacity={opacity}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}
