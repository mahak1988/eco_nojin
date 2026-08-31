/**
 * Vitest Global Setup
 * ====================
 * Global mocks for external dependencies that cannot be imported
 * in unit test environment (Three.js, WebGL, etc.)
 *
 * @module test/setup
 */

import { vi } from 'vitest';

// ─────────────────────────────────────────────────────────────────────
// Mock: lib/terrainGenerator
// ─────────────────────────────────────────────────────────────────────
// This module depends on heavy terrain processing logic.
// We provide deterministic mocks for unit testing.

vi.mock('../src/lib/terrainGenerator', () => ({
  WORLD_SIZE: 20,
  HEIGHT_SCALE: 10,
  worldToGrid: (coord: number, size: number): number => {
    // Simple linear mapping: world [-10, 10] → grid [0, size-1]
    const normalized = (coord + 10) / 20;
    return Math.round(normalized * (size - 1));
  },
  terrainColor: (): [number, number, number] => [0.3, 0.5, 0.2],
  moistureColor: (): [number, number, number] => [0.2, 0.4, 0.8],
  rootColor: (): [number, number, number] => [0.5, 0.3, 0.1],
  groundwaterColor: (): [number, number, number] => [0.1, 0.3, 0.7],
  generateTerrain: () => ({
    width: 10,
    height: 10,
    elevation: Array(10)
      .fill(0)
      .map(() => Array(10).fill(50)),
    moisture: Array(10)
      .fill(0)
      .map(() => Array(10).fill(0.5)),
    minElevation: 0,
    maxElevation: 100,
  }),
}));

// ─────────────────────────────────────────────────────────────────────
// Mock: Three.js & React Three Fiber
// ─────────────────────────────────────────────────────────────────────
// Only mock what's needed for unit tests (not rendering tests)

vi.mock('three', () => ({
  default: {
    PlaneGeometry: class {},
    Vector3: class {
      constructor(
        public x = 0,
        public y = 0,
        public z = 0
      ) {}
    },
    BufferAttribute: class {},
    DoubleSide: 2,
    MOUSE: { ROTATE: 0, DOLLY: 1, PAN: 2 },
    TOUCH: { ROTATE: 0, DOLLY_PAN: 1 },
    Texture: class {},
    TextureLoader: class {
      load() {}
      setCrossOrigin() {}
    },
  },
  PlaneGeometry: class {},
  Vector3: class {
    constructor(
      public x = 0,
      public y = 0,
      public z = 0
    ) {}
  },
  BufferAttribute: class {},
  DoubleSide: 2,
  MOUSE: { ROTATE: 0, DOLLY: 1, PAN: 2 },
  TOUCH: { ROTATE: 0, DOLLY_PAN: 1 },
  Texture: class {},
  TextureLoader: class {
    load() {}
    setCrossOrigin() {}
  },
}));

// ─────────────────────────────────────────────────────────────────────
// Mock: @react-three/fiber
// ─────────────────────────────────────────────────────────────────────

vi.mock('@react-three/fiber', () => ({
  Canvas: () => null,
  useFrame: () => {},
  useThree: () => ({
    camera: {
      position: { set: () => {} },
      lookAt: () => {},
    },
  }),
}));

// ─────────────────────────────────────────────────────────────────────
// Mock: @react-three/drei
// ─────────────────────────────────────────────────────────────────────

vi.mock('@react-three/drei', () => ({
  Html: ({ children }: { children: React.ReactNode }) => children,
  Line: () => null,
  OrbitControls: () => null,
  Sky: () => null,
  Grid: () => null,
  PerspectiveCamera: () => null,
  useTexture: () => null,
}));

// ─────────────────────────────────────────────────────────────────────
// Mock: @react-three/postprocessing
// ─────────────────────────────────────────────────────────────────────

vi.mock('@react-three/postprocessing', () => ({
  EffectComposer: ({ children }: { children: React.ReactNode }) => children,
  Bloom: () => null,
  Vignette: () => null,
}));
