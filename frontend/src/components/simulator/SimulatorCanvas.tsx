import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import * as THREE from 'three';
import { SimulatorScene } from './SimulatorScene';
import { useSimulatorStore } from './simulatorStore';
import { Spin } from 'antd';

/**
 * The R3F Canvas wrapper with adaptive DPR based on quality setting.
 * Wrapped by SimulatorErrorBoundary from the page level.
 */
export function SimulatorCanvas() {
  const quality = useSimulatorStore((s) => s.quality);
  const timeOfDay = useSimulatorStore((s) => s.timeOfDay);

  const dpr: [number, number] = quality === 'high'
    ? [1.5, 2]
    : quality === 'medium'
    ? [1, 1.5]
    : [0.75, 1];

  return (
    <Suspense fallback={
      <div style={{
        width: '100%', height: '100vh',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#0a0f1c',
      }}>
        <Spin size="large" tip="در حال بارگذاری شبیه‌ساز..." />
      </div>
    }>
      <Canvas
        shadows={quality !== 'low'}
        camera={{ position: [120, 70, 120], fov: 60, near: 0.5, far: 5000 }}
        gl={{
          antialias: true,
          powerPreference: 'high-performance',
          alpha: false,
        }}
        dpr={dpr}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = timeOfDay === 'night' ? 0.7 : 1.0;
          gl.outputColorSpace = THREE.SRGBColorSpace;
          gl.shadowMap.enabled = quality !== 'low';
          gl.shadowMap.type = THREE.PCFSoftShadowMap;
        }}
      >
        <SimulatorScene />
      </Canvas>
    </Suspense>
  );
}
