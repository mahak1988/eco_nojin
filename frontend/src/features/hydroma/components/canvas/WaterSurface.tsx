/**
 * WaterSurface Component
 * =======================
 * Animated water surface with wave-like motion.
 *
 * Features:
 * - Semi-transparent blue water material
 * - Oscillating Y position (wave motion)
 * - Oscillating opacity (shimmer effect)
 * - Positioned at configurable water level
 *
 * @module features/hydroma/components/canvas/WaterSurface
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { WORLD_SIZE, HEIGHT_SCALE } from '../../../../lib/terrainGenerator';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface WaterSurfaceProps {
  /** Normalized water level (0-1) */
  levelNorm: number;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function WaterSurface({ levelNorm }: WaterSurfaceProps) {
  const meshRef = useRef<THREE.Mesh>(null!);
  const matRef = useRef<THREE.MeshStandardMaterial>(null!);

  // Animate water level and opacity
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();

    if (matRef.current) {
      matRef.current.opacity = 0.5 + 0.1 * Math.sin(t * 0.9);
    }

    if (meshRef.current) {
      const baseY = levelNorm * HEIGHT_SCALE;
      meshRef.current.position.y = baseY + 0.4 * Math.sin(t * 0.5);
    }
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[WORLD_SIZE * 0.98, WORLD_SIZE * 0.98]} />
      <meshStandardMaterial
        ref={matRef}
        color="#2f6f9f"
        transparent
        opacity={0.55}
        metalness={0.35}
        roughness={0.12}
      />
    </mesh>
  );
}
