import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const fillLightRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, fogDensity, intensity } = useWeatherStore();

  // Configure ultra-quality shadows
  useFrame(() => {
    if (sunRef.current) {
      const shadow = sunRef.current.shadow;
      shadow.mapSize.width = 4096;  // Ultra HD shadows
      shadow.mapSize.height = 4096;
      shadow.camera.near = 1;
      shadow.camera.far = 1500;
      shadow.camera.left = -400;
      shadow.camera.right = 400;
      shadow.camera.top = 400;
      shadow.camera.bottom = -400;
      shadow.bias = -0.0001;  // Reduced shadow acne
      shadow.normalBias = 0.05;
      shadow.radius = 3;  // Soft shadow edges
      shadow.blurSamples = 16;  // High-quality soft shadows
    }
  });

  // Dynamic fog with VOLUMETRIC density
  useFrame(({ scene }) => {
    if (!scene.fog) {
      scene.fog = new THREE.FogExp2('#cccccc', 0.005);
    }
    const fog = scene.fog as THREE.FogExp2;
    
    let targetDensity = fogDensity * 0.005;
    let fogColor = '#cccccc';
    
    if (condition === 'dust') {
      targetDensity = 0.015 + intensity * 0.02;
      fogColor = '#8b6f47';
    } else if (condition === 'storm') {
      targetDensity = 0.012 + intensity * 0.015;
      fogColor = '#4a5568';
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
    
    fog.density += (targetDensity - fog.density) * 0.08;
    fog.color.lerp(new THREE.Color(fogColor), 0.08);
    scene.background = fog.color.clone();
  });

  const sunIntensity = (() => {
    let base = 2.0;  // Increased for physically correct lights
    if (timeOfDay === 'night') base = 0.15;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 1.0;
    if (condition === 'dust') base *= 0.2 * (1 - intensity * 0.5);
    if (condition === 'storm') base *= 0.15;
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

  const skyRayleigh = (() => {
    if (condition === 'dust') return 8;
    if (condition === 'storm') return 6;
    if (condition === 'rain') return 4;
    return 2;
  })();

  const skyMieCoefficient = (() => {
    if (condition === 'dust') return 0.15;
    if (condition === 'storm') return 0.1;
    return 0.005;
  })();

  return (
    <>
      {/* Main sun - Ultra HD shadows */}
      <directionalLight
        ref={sunRef}
        position={sunPosition}
        intensity={sunIntensity}
        color={sunColor}
        castShadow
      />

      {/* Fill light (reduces harsh shadows) */}
      <directionalLight
        ref={fillLightRef}
        position={[-sunPosition[0] * 0.5, sunPosition[1] * 0.3, -sunPosition[2] * 0.5]}
        intensity={sunIntensity * 0.15}
        color={sunColor}
      />

      {/* Ambient light */}
      <ambientLight 
        intensity={(() => {
          let base = timeOfDay === 'night' ? 0.2 : 0.5;
          if (condition === 'dust' || condition === 'storm') base *= 0.3;
          return base;
        })()} 
        color={sunColor} 
      />

      {/* Hemisphere light for natural sky/ground color */}
      <hemisphereLight 
        args={[
          condition === 'dust' ? '#8b6f47' : '#b8d4e8',
          condition === 'drought' ? '#8b6f47' : '#4a7c3a',
          condition === 'dust' || condition === 'storm' ? 0.2 : 0.5
        ]} 
      />

      {/* Enhanced Sky - farther distance, better resolution */}
      {timeOfDay !== 'night' && (
        <Sky
          distance={1000000}  // 1M distance for deeper sky
          sunPosition={sunPosition}
          inclination={0.5}
          azimuth={0.25}
          mieCoefficient={skyMieCoefficient}
          mieDirectionalG={condition === 'dust' ? 0.9 : 0.8}
          rayleigh={skyRayleigh}
          turbidity={condition === 'dust' ? 20 : condition === 'storm' ? 15 : 8}
        />
      )}

      {/* Stars at night - more stars, bigger radius */}
      {timeOfDay === 'night' && (
        <Stars 
          radius={800} 
          depth={100} 
          count={8000} 
          factor={6} 
          saturation={0.2}
          fade 
          speed={0.5}
        />
      )}

      {/* Storm clouds */}
      {(condition === 'storm' || condition === 'rain') && (
        <>
          <Cloud position={[-60, 80, -100]} speed={0.6} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} segments={40} />
          <Cloud position={[80, 90, -120]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} segments={40} />
          <Cloud position={[0, 85, -150]} speed={0.7} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} segments={40} />
        </>
      )}

      {/* Dust clouds */}
      {condition === 'dust' && (
        <>
          <Cloud position={[-40, 25, -50]} speed={0.8} opacity={0.7} color="#8b6f47" segments={30} />
          <Cloud position={[60, 30, -70]} speed={0.9} opacity={0.8} color="#a0826b" segments={30} />
        </>
      )}
    </>
  );
}
