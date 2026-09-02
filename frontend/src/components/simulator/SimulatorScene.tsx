import { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { Sky } from './primitives/Sky';
import { Terrain } from './primitives/Terrain';
import { Water } from './primitives/Water';
import { Clouds } from './primitives/Clouds';
import { useSimulatorStore, TimeOfDay } from './simulatorStore';

/**
 * Moving sun: full day cycle over 180s when autoSunCycle is on.
 * Sun color/intensity adapts to time of day and weather.
 */
function Sun() {
  const { timeOfDay, weather, autoSunCycle, setTimeOfDay } = useSimulatorStore();
  const lightRef = useRef<THREE.DirectionalLight>(null);
  const cycle = useRef(0.30);

  useFrame((_, delta) => {
    if (!lightRef.current) return;

    if (autoSunCycle) {
      cycle.current = (cycle.current + delta / 180) % 1;
      const el = Math.sin(cycle.current * Math.PI * 2);
      const az = cycle.current * Math.PI * 2;
      const R = 500;
      const horiz = Math.sqrt(Math.max(0.05, 1 - el * el));
      lightRef.current.position.set(
        Math.cos(az) * horiz * R,
        el * R,
        Math.sin(az) * horiz * R * 0.5
      );

      let phase: TimeOfDay;
      if (el > 0.35) phase = 'day';
      else if (el > 0) phase = Math.cos(az) > 0 ? 'dawn' : 'dusk';
      else phase = 'night';
      if (phase !== timeOfDay) setTimeOfDay(phase);
    }

    // Intensity & color by phase + weather
    let intensity = 2.5;
    let color = '#fff3d6';
    if (timeOfDay === 'night') { intensity = 0.15; color = '#4a6fa5'; }
    else if (timeOfDay === 'dawn') { intensity = 1.1; color = '#ffb347'; }
    else if (timeOfDay === 'dusk') { intensity = 1.1; color = '#ff6b6b'; }
    if (weather === 'storm') intensity *= 0.2;
    if (weather === 'rain')  intensity *= 0.5;
    if (weather === 'dust')  intensity *= 0.3;

    lightRef.current.intensity = intensity;
    lightRef.current.color.lerp(new THREE.Color(color), 0.05);
  });

  return (
    <directionalLight
      ref={lightRef}
      position={[200, 300, 100]}
      castShadow
      shadow-mapSize={[2048, 2048]}
      shadow-camera-left={-200}
      shadow-camera-right={200}
      shadow-camera-top={200}
      shadow-camera-bottom={-200}
      shadow-camera-near={1}
      shadow-camera-far={1500}
      shadow-bias={-0.0002}
    />
  );
}

export function SimulatorScene() {
  const { timeOfDay, weather } = useSimulatorStore();

  // Fog color based on time + weather
  const fogColor = (() => {
    if (timeOfDay === 'night') return '#0a1520';
    if (timeOfDay === 'dawn') return '#ffd9b0';
    if (timeOfDay === 'dusk') return '#ffc9a0';
    if (weather === 'dust') return '#a08055';
    if (weather === 'storm') return '#5a6675';
    if (weather === 'rain') return '#93a5b5';
    if (weather === 'snow') return '#dfe5ee';
    return '#cfe0ee';
  })();

  return (
    <>
      <fog attach="fog" args={[fogColor, 200, 2000]} />

      <Sun />
      <ambientLight intensity={timeOfDay === 'night' ? 0.2 : 0.4} />
      <hemisphereLight
        args={[weather === 'dust' ? '#8b6f47' : '#bfe0f0', '#4a7c3a', 0.5]}
      />

      <Sky />
      <Terrain />
      <Water />
      <Clouds />

      <OrbitControls
        makeDefault
        enablePan
        enableZoom
        enableRotate
        minDistance={20}
        maxDistance={500}
        maxPolarAngle={Math.PI / 2.1}
        target={[0, 0, 0]}
        enableDamping
        dampingFactor={0.05}
      />
    </>
  );
}
