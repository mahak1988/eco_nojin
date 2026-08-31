/**
 * CameraTour Component
 * =====================
 * Automatic cinematic camera tour around the scene.
 *
 * Features:
 * - Orbital camera motion with varying radius
 * - Oscillating height for dynamic feel
 * - Always looking at scene center
 * - Only active when enabled (for performance)
 *
 * @module features/hydroma/components/canvas/CameraTour
 */

import { useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface CameraTourProps {
  /** Whether tour is active */
  active: boolean;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function CameraTour({ active }: CameraTourProps) {
  const { camera } = useThree();
  const timeRef = useRef(0);

  useFrame((_, dt) => {
    if (!active) return;

    timeRef.current += dt;
    const t = timeRef.current;

    // Orbital motion with varying radius
    const ang = t * 0.18;
    const radius = 1150 - 350 * (0.5 + 0.5 * Math.sin(t * 0.1));
    const height = 520 - 240 * (0.5 + 0.5 * Math.cos(t * 0.13));

    camera.position.set(Math.cos(ang) * radius, height, Math.sin(ang) * radius);

    // Always look at scene center
    camera.lookAt(0, 30, 0);
  });

  return null;
}
