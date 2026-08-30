/**
 * CameraController Component
 * ===========================
 * Applies view mode presets to the camera.
 *
 * Features:
 * - 3D mode: lets OrbitControls handle freely
 * - 2D-top: top-down orthographic-like view
 * - 2D-side: side view
 * - Cross-section: frontal cross-section view
 * - Smooth transitions via useEffect
 *
 * @module features/hydroma/components/canvas/CameraController
 */

import { useMemo, useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import { VIEW_MODE_POSITIONS } from '../../constants';
import type { ViewMode } from '../../types';

// ─────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────

export interface CameraControllerProps {
  /** Current view mode */
  viewMode: ViewMode;
}

// ─────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────

interface CameraTarget {
  pos: [number, number, number];
  lookAt: [number, number, number];
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export function CameraController({ viewMode }: CameraControllerProps) {
  const { camera } = useThree();

  // Calculate target position based on view mode
  const target = useMemo<CameraTarget | null>(() => {
    const preset = VIEW_MODE_POSITIONS[viewMode];
    if (!preset) return null;
    return preset;
  }, [viewMode]);

  // Apply camera position when target changes
  useEffect(() => {
    if (target) {
      camera.position.set(target.pos[0], target.pos[1], target.pos[2]);
      camera.lookAt(target.lookAt[0], target.lookAt[1], target.lookAt[2]);
    }
  }, [target, camera]);

  return null;
}
