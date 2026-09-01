import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { CustomWater } from './CustomWater';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function WaterSystem() {
  const waterRef = useRef<THREE.Group>(null);
  const { condition, timeOfDay } = useWeatherStore();

  // Dynamic water color based on conditions
  const waterColor = (() => {
    if (condition === 'drought') return '#8b7355';
    if (condition === 'dust') return '#a0826b';
    if (timeOfDay === 'dawn') return '#ff9a6b';
    if (timeOfDay === 'dusk') return '#d85a7a';
    if (timeOfDay === 'night') return '#1a2a4a';
    return '#2a5a8a';
  })();

  // Dynamic wave height based on weather
  const waveHeight = (() => {
    if (condition === 'storm') return 0.8;
    if (condition === 'rain') return 0.4;
    return 0.2;
  })();

  // Wave speed
  const waveSpeed = condition === 'storm' ? 1.2 : condition === 'rain' ? 0.8 : 0.5;

  return (
    <group ref={waterRef}>
      {/* Main water body */}
      <CustomWater
        position={[-40, 1, -20]}
        args={[40, 40]}
        color={waterColor}
        waveHeight={waveHeight}
        waveSpeed={waveSpeed}
        segments={96}
      />
      
      {/* Additional water patch */}
      <CustomWater
        position={[30, 0.5, 40]}
        args={[25, 20]}
        color={waterColor}
        waveHeight={waveHeight * 0.7}
        waveSpeed={waveSpeed * 0.8}
        segments={64}
      />
    </group>
  );
}
