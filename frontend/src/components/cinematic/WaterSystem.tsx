import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Water } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function WaterSystem() {
  const waterRef = useRef<any>(null);
  const { condition, timeOfDay } = useWeatherStore();

  const waterColor = (() => {
    if (condition === 'drought') return '#8b7355';
    if (condition === 'dust') return '#a0826b';
    if (timeOfDay === 'dawn') return '#ffb347';
    if (timeOfDay === 'dusk') return '#ff6b6b';
    if (timeOfDay === 'night') return '#1a3a5a';
    return '#2a5a8a';
  })();

  return (
    <Water
      ref={waterRef}
      position={[-40, 1, -20]}
      rotation={[-Math.PI / 2, 0, 0]}
      args={[40, 40]}
      color={waterColor}
      waveHeight={condition === 'storm' ? 0.8 : 0.2}
      waveSpeed={0.05}
      flowSpeed={0.01}
      flowDirection={[1, 1]}
      reflectivity={0.8}
    />
  );
}
