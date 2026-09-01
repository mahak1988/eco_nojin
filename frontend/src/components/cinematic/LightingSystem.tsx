import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore, TimeOfDay } from '../../hooks/useWeatherStore';
import { useQualityStore } from '../../hooks/useQualityStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';

/**
 * Celestial system:
 *  - Moving sun: full day cycle (180s) when "حرکت خورشید" is ON
 *  - Drifting clouds: cloud group moves with wind (visible even on clear days)
 *  - Real sunshine: strong warm directional light with soft shadows at day
 */
export function LightingSystem() {
  const { timeOfDay, sunPosition, condition, intensity, windSpeed } = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);
  const enableSunCycle = useArtisticStore((s) => s.enableSunCycle);

  const cycle = useRef(0.30); // start at morning
  const acc = useRef(0);
  const [liveSun, setLiveSun] = useState<[number, number, number]>(sunPosition);
  const [livePhase, setLivePhase] = useState<TimeOfDay>(timeOfDay);
  const cloudsRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    // --- Clouds ALWAYS drift with the wind ---
    if (cloudsRef.current) {
      cloudsRef.current.position.x += delta * (2 + windSpeed * 0.4);
      if (cloudsRef.current.position.x > 260) cloudsRef.current.position.x = -260;
    }

    // --- Sun cycle ---
    if (!enableSunCycle) return;
    cycle.current = (cycle.current + delta / 180) % 1; // 180s full day
    acc.current += delta;
    if (acc.current < 0.15) return; // throttle React updates
    acc.current = 0;

    const t = cycle.current;
    const el = Math.sin(t * Math.PI * 2);       // elevation -1..1
    const az = t * Math.PI * 2;                 // azimuth
    const R = 400;
    const horiz = Math.sqrt(Math.max(0.05, 1 - el * el));
    setLiveSun([Math.cos(az) * horiz * R, el * R, Math.sin(az) * horiz * R * 0.5]);

    let ph: TimeOfDay;
    if (el > 0.35) ph = 'day';
    else if (el > 0) ph = Math.cos(az) > 0 ? 'dawn' : 'dusk';
    else ph = 'night';
    setLivePhase(ph);
  });

  const phase: TimeOfDay = enableSunCycle ? livePhase : timeOfDay;
  const sun = enableSunCycle ? liveSun : sunPosition;

  // Fog
  useFrame(({ scene }) => {
    if (!scene.fog) scene.fog = new THREE.FogExp2('#d8ecf5', 0.0012);
    const fog = scene.fog as THREE.FogExp2;
    let density = 0.0012;
    let color = '#d8ecf5';
    if (condition === 'dust')       { density = 0.016 + intensity * 0.015; color = '#a08055'; }
    else if (condition === 'storm') { density = 0.012 + intensity * 0.012; color = '#5a6675'; }
    else if (condition === 'rain')  { density = 0.005; color = '#93a5b5'; }
    else if (condition === 'snow')  { density = 0.005; color = '#dfe5ee'; }
    else if (condition === 'drought'){ density = 0.0025; color = '#d8c49a'; }
    else if (phase === 'night')     { density = 0.0015; color = '#0a1520'; }
    else if (phase === 'dawn')      { density = 0.002; color = '#ffd9b0'; }
    else if (phase === 'dusk')      { density = 0.002; color = '#ffc9a0'; }
    fog.density += (density - fog.density) * 0.06;
    fog.color.lerp(new THREE.Color(color), 0.06);
  });

  // --- Sunshine intensity & color (تابش خورشید) ---
  const sunIntensity = (() => {
    let base = 2.6; // strong daylight sunshine
    if (phase === 'night') base = 0.15;
    else if (phase === 'dawn' || phase === 'dusk') base = 1.2;
    if (condition === 'dust') base *= 0.25;
    if (condition === 'storm') base *= 0.18;
    if (condition === 'rain') base *= 0.5;
    if (condition === 'snow') base *= 0.7;
    return base;
  })();

  const sunColor = (() => {
    if (condition === 'dust') return '#d4935a';
    if (condition === 'storm') return '#8a9aa8';
    if (phase === 'dawn') return '#ffb347';
    if (phase === 'dusk') return '#ff6b6b';
    if (phase === 'night') return '#4a6fa5';
    return '#fff3d6'; // warm sunshine
  })();

  const shadowSize = tier === 'high' ? 2048 : 1024;

  return (
    <>
      <directionalLight
        position={sun}
        intensity={sunIntensity}
        color={sunColor}
        castShadow={tier !== 'low'}
        shadow-mapSize={[shadowSize, shadowSize]}
        shadow-camera-left={-400}
        shadow-camera-right={400}
        shadow-camera-top={400}
        shadow-camera-bottom={-400}
        shadow-camera-near={1}
        shadow-camera-far={1500}
        shadow-bias={-0.0001}
        shadow-normalBias={0.05}
      />
      <ambientLight intensity={phase === 'night' ? 0.2 : condition === 'dust' || condition === 'storm' ? 0.25 : 0.45} color={sunColor} />
      <hemisphereLight
        args={[
          condition === 'dust' ? '#8b6f47' : '#bfe0f0',
          '#4a7c3a',
          condition === 'dust' || condition === 'storm' ? 0.25 : 0.5,
        ]}
      />

      {phase !== 'night' && (
        <Sky
          distance={3500}
          sunPosition={sun}
          mieCoefficient={condition === 'dust' ? 0.12 : condition === 'storm' ? 0.08 : 0.005}
          rayleigh={condition === 'dust' ? 6 : condition === 'storm' ? 4 : 1.5}
          turbidity={condition === 'dust' ? 18 : condition === 'storm' ? 12 : 6}
        />
      )}

      {phase === 'night' && <Stars radius={800} depth={100} count={8000} factor={6} saturation={0.2} fade speed={0.5} />}

      {/* --- MOVING CLOUDS (حرکت ابرها) --- */}
      <group ref={cloudsRef}>
        {/* Fair-weather clouds on clear days */}
        {(condition === 'clear' || condition === 'drought') && phase !== 'night' && (
          <>
            <Cloud position={[-90, 95, -140]} speed={0.4} opacity={0.5} color="#ffffff" segments={24} />
            <Cloud position={[30, 105, -170]} speed={0.3} opacity={0.45} color="#ffffff" segments={24} />
            <Cloud position={[130, 90, -100]} speed={0.5} opacity={0.5} color="#ffffff" segments={24} />
          </>
        )}
        {(condition === 'storm' || condition === 'rain') && (
          <>
            <Cloud position={[-60, 80, -100]} speed={0.8} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} segments={30} />
            <Cloud position={[80, 90, -120]} speed={0.7} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} segments={30} />
            <Cloud position={[0, 85, -150]} speed={0.9} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} segments={30} />
          </>
        )}
        {condition === 'dust' && (
          <>
            <Cloud position={[-40, 25, -50]} speed={1.2} opacity={0.6} color="#8b6f47" segments={24} />
            <Cloud position={[60, 30, -70]} speed={1.4} opacity={0.7} color="#a0826b" segments={24} />
          </>
        )}
        {condition === 'snow' && (
          <Cloud position={[0, 90, -130]} speed={0.5} opacity={0.7} color="#dfe5ee" segments={24} />
        )}
      </group>
    </>
  );
}
