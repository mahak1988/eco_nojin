import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, fogDensity, intensity } = useWeatherStore();

  // Dynamic fog with VOLUMETRIC density for dust/storm
  useFrame(({ scene }) => {
    if (!scene.fog) {
      scene.fog = new THREE.FogExp2('#cccccc', 0.005);
    }
    const fog = scene.fog as THREE.FogExp2;
    
    let targetDensity = fogDensity * 0.005;
    let fogColor = '#cccccc';
    
    if (condition === 'dust') {
      // DUST STORM: Heavy volumetric fog + brown tint
      targetDensity = 0.015 + intensity * 0.02;  // Very dense!
      fogColor = '#8b6f47';  // Brown dust
    } else if (condition === 'storm') {
      // STORM: Dense grey fog + darkness
      targetDensity = 0.012 + intensity * 0.015;
      fogColor = '#4a5568';  // Dark storm grey
    } else if (condition === 'snow') {
      targetDensity = 0.008;
      fogColor = '#d8dce8';
    } else if (condition === 'drought') {
      targetDensity = 0.004;
      fogColor = '#c4a574';
    } else if (condition === 'rain') {
      targetDensity = 0.008;
      fogColor = '#8a9aa8';
    } else if (timeOfDay === 'night') {
      fogColor = '#0a1520';
      targetDensity = 0.003;
    } else if (timeOfDay === 'dawn') {
      fogColor = '#ffb88c';
    } else if (timeOfDay === 'dusk') {
      fogColor = '#ff7e5f';
    }
    
    // Smooth interpolation
    fog.density += (targetDensity - fog.density) * 0.08;
    fog.color.lerp(new THREE.Color(fogColor), 0.08);
    scene.background = fog.color.clone();
  });

  // Sun intensity heavily reduced during dust/storm
  const sunIntensity = (() => {
    let base = 1.5;
    if (timeOfDay === 'night') base = 0.1;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.8;
    
    // DUST: Sun barely visible (orange/brown filtered)
    if (condition === 'dust') base *= 0.2 * (1 - intensity * 0.5);
    // STORM: Sun blocked by clouds
    if (condition === 'storm') base *= 0.15;
    if (condition === 'rain') base *= 0.5;
    if (condition === 'snow') base *= 0.7;
    
    return base;
  })();

  const sunColor = (() => {
    if (condition === 'dust') return '#d4935a';  // Orange-brown through dust
    if (condition === 'storm') return '#8a9aa8';  // Grey diffused
    if (timeOfDay === 'dawn') return '#ffb347';
    if (timeOfDay === 'dusk') return '#ff6b6b';
    if (timeOfDay === 'night') return '#4a6fa5';
    return '#fff8e7';
  })();

  // Sky parameters based on weather
  const skyRayleigh = (() => {
    if (condition === 'dust') return 8;  // Heavy scattering
    if (condition === 'storm') return 6;
    if (condition === 'rain') return 4;
    return 2;
  })();

  const skyMieCoefficient = (() => {
    if (condition === 'dust') return 0.15;  // Large particles
    if (condition === 'storm') return 0.1;
    return 0.005;
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
        shadow-camera-left={-200}
        shadow-camera-right={200}
        shadow-camera-top={200}
        shadow-camera-bottom={-200}
        shadow-camera-near={0.1}
        shadow-camera-far={800}
      />

      {/* Ambient light - reduced during storms */}
      <ambientLight 
        intensity={(() => {
          let base = timeOfDay === 'night' ? 0.15 : 0.4;
          if (condition === 'dust' || condition === 'storm') base *= 0.3;
          return base;
        })()} 
        color={sunColor} 
      />

      {/* Hemisphere light */}
      <hemisphereLight 
        args={[
          condition === 'dust' ? '#8b6f47' : '#87ceeb',
          '#3d5a3d',
          condition === 'dust' || condition === 'storm' ? 0.15 : 0.3
        ]} 
      />

      {/* Sky - darkened for dust/storm */}
      {timeOfDay !== 'night' && (
        <Sky
          distance={450000}
          sunPosition={sunPosition}
          inclination={0.5}
          azimuth={0.25}
          mieCoefficient={skyMieCoefficient}
          mieDirectionalG={condition === 'dust' ? 0.9 : 0.8}
          rayleigh={skyRayleigh}
          turbidity={condition === 'dust' ? 20 : condition === 'storm' ? 15 : 10}
        />
      )}

      {/* Stars at night */}
      {timeOfDay === 'night' && <Stars radius={500} depth={80} count={5000} factor={6} fade />}

      {/* Storm clouds - dark and dense */}
      {(condition === 'storm' || condition === 'rain') && (
        <>
          <Cloud position={[-60, 80, -100]} speed={0.6} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} />
          <Cloud position={[80, 90, -120]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} />
          <Cloud position={[0, 85, -150]} speed={0.7} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} />
          <Cloud position={[-40, 75, -80]} speed={0.4} opacity={0.8} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} />
          <Cloud position={[60, 70, -60]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} />
        </>
      )}

      {/* Dust clouds - brown and low */}
      {condition === 'dust' && (
        <>
          <Cloud position={[-40, 25, -50]} speed={0.8} opacity={0.7} color="#8b6f47" />
          <Cloud position={[60, 30, -70]} speed={0.9} opacity={0.8} color="#a0826b" />
          <Cloud position={[0, 20, -90]} speed={1.0} opacity={0.75} color="#8b6f47" />
        </>
      )}
    </>
  );
}
