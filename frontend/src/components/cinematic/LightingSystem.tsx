import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, intensity } = useWeatherStore();

  // Fog ONLY (never override scene.background - let Sky render!)
  useFrame(({ scene }) => {
    if (!scene.fog) scene.fog = new THREE.FogExp2('#cfe0ee', 0.0012);
    const fog = scene.fog as THREE.FogExp2;

    let density = 0.0012;
    let color = '#cfe0ee';

    if (condition === 'dust')       { density = 0.016 + intensity * 0.015; color = '#a08055'; }
    else if (condition === 'storm') { density = 0.012 + intensity * 0.012; color = '#5a6675'; }
    else if (condition === 'rain')  { density = 0.005; color = '#93a5b5'; }
    else if (condition === 'snow')  { density = 0.005; color = '#dfe5ee'; }
    else if (condition === 'drought'){ density = 0.0025; color = '#d8c49a'; }
    else if (timeOfDay === 'night') { density = 0.0015; color = '#0a1520'; }
    else if (timeOfDay === 'dawn')  { density = 0.002; color = '#ffd9b0'; }
    else if (timeOfDay === 'dusk')  { density = 0.002; color = '#ffc9a0'; }

    fog.density += (density - fog.density) * 0.06;
    fog.color.lerp(new THREE.Color(color), 0.06);
  });

  const sunIntensity = (() => {
    let base = 2.2;
    if (timeOfDay === 'night') base = 0.15;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 1.1;
    if (condition === 'dust') base *= 0.25;
    if (condition === 'storm') base *= 0.18;
    if (condition === 'rain') base *= 0.5;
    if (condition === 'snow') base *= 0.7;
    return base;
  })();

  const sunColor = (() => {
    if (condition === 'dust') return '#d4935a';
    if (condition === 'storm') return '#8a9aa8';
    if (timeOfDay === 'dawn') return '#ffb347';
    if (timeOfDay === 'dusk') return '#ff6b6b';
    if (timeOfDay === 'night') return '#4a6fa5';
    return '#fff8e7';
  })();

  return (
    <>
      <directionalLight
        ref={sunRef}
        position={sunPosition}
        intensity={sunIntensity}
        color={sunColor}
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-400}
        shadow-camera-right={400}
        shadow-camera-top={400}
        shadow-camera-bottom={-400}
        shadow-camera-near={1}
        shadow-camera-far={1500}
        shadow-bias={-0.0001}
        shadow-normalBias={0.05}
      />
      <ambientLight intensity={timeOfDay === 'night' ? 0.2 : condition === 'dust' || condition === 'storm' ? 0.25 : 0.45} color={sunColor} />
      <hemisphereLight
        args={[
          condition === 'dust' ? '#8b6f47' : '#b8d4e8',
          '#4a7c3a',
          condition === 'dust' || condition === 'storm' ? 0.25 : 0.5,
        ]}
      />

      {/* CRITICAL FIX: distance must be < camera.far (5000) or Sky is clipped! */}
      {timeOfDay !== 'night' && (
        <Sky
          distance={3500}
          sunPosition={sunPosition}
          mieCoefficient={condition === 'dust' ? 0.12 : condition === 'storm' ? 0.08 : 0.005}
          rayleigh={condition === 'dust' ? 6 : condition === 'storm' ? 4 : 1.5}
          turbidity={condition === 'dust' ? 18 : condition === 'storm' ? 12 : 6}
        />
      )}

      {timeOfDay === 'night' && <Stars radius={800} depth={100} count={8000} factor={6} saturation={0.2} fade speed={0.5} />}

      {(condition === 'storm' || condition === 'rain') && (
        <>
          <Cloud position={[-60, 80, -100]} speed={0.6} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} segments={40} />
          <Cloud position={[80, 90, -120]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} segments={40} />
          <Cloud position={[0, 85, -150]} speed={0.7} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} segments={40} />
        </>
      )}
      {condition === 'dust' && (
        <>
          <Cloud position={[-40, 25, -50]} speed={0.8} opacity={0.6} color="#8b6f47" segments={30} />
          <Cloud position={[60, 30, -70]} speed={0.9} opacity={0.7} color="#a0826b" segments={30} />
        </>
      )}
    </>
  );
}
