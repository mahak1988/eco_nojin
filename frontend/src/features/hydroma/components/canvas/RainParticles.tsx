/**
 * RainParticles Component
 * ========================
 * Particle system for rain visualization.
 *
 * Features:
 * - Configurable particle count (default: 1400)
 * - Random initial positions
 * - Gravity-based downward motion
 * - Wrap-around when reaching ground
 * - Transparent blue material
 *
 * @module features/hydroma/components/canvas/RainParticles
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { WORLD_SIZE } from '../../../../lib/terrainGenerator';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface RainParticlesProps {
  /** Number of rain particles */
  count?: number;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function RainParticles({ count = 1400 }: RainParticlesProps) {
  const pointsRef = useRef<THREE.Points>(null!);

  // Generate random initial positions
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * WORLD_SIZE;
      arr[i * 3 + 1] = Math.random() * 420;
      arr[i * 3 + 2] = (Math.random() - 0.5) * WORLD_SIZE;
    }
    return arr;
  }, [count]);

  // Animate particles falling
  useFrame((_, dt) => {
    const geo = pointsRef.current?.geometry as THREE.BufferGeometry | undefined;
    if (!geo) return;

    const pos = geo.attributes.position as THREE.BufferAttribute;

    for (let i = 0; i < pos.count; i++) {
      let y = pos.getY(i) - dt * 160;
      // Wrap around to top when hitting ground
      if (y < 0) y = 420;
      pos.setY(i, y);
    }

    pos.needsUpdate = true;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={2.2} color="#a5c8e8" transparent opacity={0.55} sizeAttenuation />
    </points>
  );
}
