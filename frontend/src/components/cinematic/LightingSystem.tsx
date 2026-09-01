import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, fogDensity } = useWeatherStore();

  // Dynamic fog based on weather
  useFrame(({ scene }) => {
    if (!scene.fog) {
      scene.fog = new THREE.FogExp2('#cccccc', 0.01);
    }
    const fog = scene.fog as THREE.FogExp2;
    
    let targetDensity = fogDensity * 0.02;
    let fogColor = '#cccccc';
    
    if (condition === 'dust') {
      targetDensity = 0.04;
      fogColor = '#c9a66b';
    } else if (condition === 'snow') {
      targetDensity = 0.025;
      fogColor = '#e8e8f0';
    } else if (condition === 'drought') {
      targetDensity = 0.015;
      fogColor = '#d4b896';
    } else if (condition === 'rain' || condition === 'storm') {
      targetDensity = 0.03;
      fogColor = '#8a9aa8';
    } else if (timeOfDay === 'night') {
      fogColor = '#0a1520';
    } else if (timeOfDay === 'dawn') {
      fogColor = '#ffb88c';
    } else if (timeOfDay === 'dusk') {
      fogColor = '#ff7e5f';
    }
    
    fog.density += (targetDensity - fog.density) * 0.05;
    fog.color.lerp(new THREE.Color(fogColor), 0.05);
    scene.background = fog.color.clone();
  });

  // Sun intensity based on time and weather
  const sunIntensity = (() => {
    let base = 1.5;
    if (timeOfDay === 'night') base = 0.1;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.8;
    if (condition === 'rain' || condition === 'storm') base *= 0.5;
    if (condition === 'dust') base *= 0.6;
    if (condition === 'snow') base *= 0.7;
    return base;
  })();

  const sunColor = (() => {
    if (timeOfDay === 'dawn') return '#ffb347';
    if (timeOfDay === 'dusk') return '#ff6b6b';
    if (timeOfDay === 'night') return '#4a6fa5';
    return '#fff8e7';
  })();

  return (
    <>
      {/* Main sun light */}
      <directionalLight
        ref={sunRef}
        position={sunPosition}
        intensity={sunIntensity}
        color={sunColor}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-100}
        shadow-camera-right={100}
        shadow-camera-top={100}
        shadow-camera-bottom={-100}
        shadow-camera-near={0.1}
        shadow-camera-far={500}
      />

      {/* Ambient light */}
      <ambientLight intensity={timeOfDay === 'night' ? 0.15 : 0.4} color={sunColor} />

      {/* Hemisphere light for natural lighting */}
      <hemisphereLight args={['#87ceeb', '#3d5a3d', 0.3]} />

      {/* Sky */}
      {timeOfDay !== 'night' && (
        <Sky
          distance={450000}
          sunPosition={sunPosition}
          inclination={0.5}
          azimuth={0.25}
          mieCoefficient={condition === 'dust' ? 0.1 : 0.005}
          rayleigh={condition === 'dust' ? 5 : 2}
        />
      )}

      {/* Stars at night */}
      {timeOfDay === 'night' && <Stars radius={300} depth={60} count={5000} factor={6} fade />}

      {/* Clouds */}
      {(condition === 'rain' || condition === 'storm' || condition === 'snow') && (
        <>
          <Cloud position={[-20, 40, -30]} speed={0.4} opacity={0.8} color="#8a9aa8" />
          <Cloud position={[30, 45, -50]} speed={0.3} opacity={0.7} color="#7a8a98" />
          <Cloud position={[0, 42, -70]} speed={0.5} opacity={0.9} color="#6a7a88" />
        </>
      )}
    </>
  );
}
