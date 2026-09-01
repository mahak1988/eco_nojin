import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// ============ RAIN SYSTEM (Enhanced for Storm) ============
function Rain() {
  const { intensity, windSpeed, windDirection, condition } = useWeatherStore();
  const isStorm = condition === 'storm';
  const count = isStorm ? 15000 : 5000;
  const meshRef = useRef<THREE.Points>(null);

  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 600;
      pos[i * 3 + 1] = Math.random() * 150 + 30;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 600;
      vel[i * 3 + 1] = isStorm ? -4 - Math.random() * 2 : -1.5 - Math.random() * 0.5;
    }
    return [pos, vel];
  }, [count, isStorm]);

  useFrame(() => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const windX = Math.cos((windDirection * Math.PI) / 180) * windSpeed * (isStorm ? 0.08 : 0.01);
    const windZ = Math.sin((windDirection * Math.PI) / 180) * windSpeed * (isStorm ? 0.08 : 0.01);
    
    for (let i = 0; i < count; i++) {
      arr[i * 3] += windX;
      arr[i * 3 + 1] += velocities[i * 3 + 1];
      arr[i * 3 + 2] += windZ;
      
      if (arr[i * 3 + 1] < 0) {
        arr[i * 3] = (Math.random() - 0.5) * 600;
        arr[i * 3 + 1] = Math.random() * 30 + 150;
        arr[i * 3 + 2] = (Math.random() - 0.5) * 600;
      }
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={isStorm ? 0.25 : 0.15}
        color={isStorm ? "#c8d8e8" : "#a0c4ff"}
        transparent
        opacity={0.7 * intensity}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

// ============ DUST STORM (Volumetric) ============
function DustStorm() {
  const { intensity, windSpeed, windDirection } = useWeatherStore();
  
  // Multiple layers of dust for volumetric effect
  const dustLayers = useMemo(() => {
    const layers = [];
    
    // Layer 1: Fine particles (high density)
    const count1 = 8000;
    const pos1 = new Float32Array(count1 * 3);
    const vel1 = new Float32Array(count1 * 3);
    for (let i = 0; i < count1; i++) {
      pos1[i * 3] = (Math.random() - 0.5) * 800;
      pos1[i * 3 + 1] = Math.random() * 60;
      pos1[i * 3 + 2] = (Math.random() - 0.5) * 800;
      vel1[i * 3 + 1] = (Math.random() - 0.5) * 0.3;
    }
    layers.push({ count: count1, positions: pos1, velocities: vel1, size: 0.6, opacity: 0.4, speed: 1.5 });
    
    // Layer 2: Medium particles (swirling)
    const count2 = 4000;
    const pos2 = new Float32Array(count2 * 3);
    const vel2 = new Float32Array(count2 * 3);
    for (let i = 0; i < count2; i++) {
      pos2[i * 3] = (Math.random() - 0.5) * 800;
      pos2[i * 3 + 1] = Math.random() * 40 + 10;
      pos2[i * 3 + 2] = (Math.random() - 0.5) * 800;
      vel2[i * 3 + 1] = (Math.random() - 0.5) * 0.5;
    }
    layers.push({ count: count2, positions: pos2, velocities: vel2, size: 1.0, opacity: 0.5, speed: 1.2 });
    
    // Layer 3: Large debris (slow, heavy)
    const count3 = 1500;
    const pos3 = new Float32Array(count3 * 3);
    const vel3 = new Float32Array(count3 * 3);
    for (let i = 0; i < count3; i++) {
      pos3[i * 3] = (Math.random() - 0.5) * 800;
      pos3[i * 3 + 1] = Math.random() * 30;
      pos3[i * 3 + 2] = (Math.random() - 0.5) * 800;
      vel3[i * 3 + 1] = (Math.random() - 0.5) * 0.2;
    }
    layers.push({ count: count3, positions: pos3, velocities: vel3, size: 1.5, opacity: 0.3, speed: 0.8 });
    
    return layers;
  }, []);
  
  const refs = useRef<(THREE.Points | null)[]>([]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const windX = Math.cos((windDirection * Math.PI) / 180) * windSpeed * 0.15;
    const windZ = Math.sin((windDirection * Math.PI) / 180) * windSpeed * 0.15;
    
    dustLayers.forEach((layer, layerIdx) => {
      const mesh = refs.current[layerIdx];
      if (!mesh) return;
      
      const posAttr = mesh.geometry.attributes.position as THREE.BufferAttribute;
      const arr = posAttr.array as Float32Array;
      
      for (let i = 0; i < layer.count; i++) {
        const turbulence = Math.sin(t * 2 + i * 0.1) * 0.5;
        arr[i * 3] += windX * layer.speed + turbulence * 0.3;
        arr[i * 3 + 1] += layer.velocities[i * 3 + 1] + Math.sin(t * 3 + i) * 0.1;
        arr[i * 3 + 2] += windZ * layer.speed + Math.cos(t * 2 + i) * 0.3;
        
        // Wrap around
        if (arr[i * 3] > 400) arr[i * 3] = -400;
        if (arr[i * 3] < -400) arr[i * 3] = 400;
        if (arr[i * 3 + 1] < 0) arr[i * 3 + 1] = 60;
        if (arr[i * 3 + 1] > 80) arr[i * 3 + 1] = 0;
        if (arr[i * 3 + 2] > 400) arr[i * 3 + 2] = -400;
        if (arr[i * 3 + 2] < -400) arr[i * 3 + 2] = 400;
      }
      posAttr.needsUpdate = true;
    });
  });

  return (
    <group>
      {dustLayers.map((layer, i) => (
        <points key={i} ref={(el) => { refs.current[i] = el; }}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={layer.count}
              array={layer.positions}
              itemSize={3}
            />
          </bufferGeometry>
          <pointsMaterial
            size={layer.size}
            color="#c9a66b"
            transparent
            opacity={layer.opacity * intensity}
            depthWrite={false}
            sizeAttenuation
            blending={THREE.NormalBlending}
          />
        </points>
      ))}
    </group>
  );
}

// ============ SNOW (Enhanced) ============
function Snow() {
  const { intensity, windSpeed } = useWeatherStore();
  const count = 5000;
  const meshRef = useRef<THREE.Points>(null);
  const offsets = useMemo(() => new Float32Array(count).map(() => Math.random() * Math.PI * 2), []);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 800;
      pos[i * 3 + 1] = Math.random() * 150 + 30;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 800;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const t = state.clock.elapsedTime;
    
    for (let i = 0; i < count; i++) {
      arr[i * 3] += Math.sin(t + offsets[i]) * 0.03 + windSpeed * 0.003;
      arr[i * 3 + 1] -= 0.2;
      arr[i * 3 + 2] += Math.cos(t + offsets[i]) * 0.03;
      
      if (arr[i * 3 + 1] < 0) {
        arr[i * 3] = (Math.random() - 0.5) * 800;
        arr[i * 3 + 1] = 150;
        arr[i * 3 + 2] = (Math.random() - 0.5) * 800;
      }
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={0.4}
        color="#ffffff"
        transparent
        opacity={0.9 * intensity}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

// ============ WEATHER CONTROLLER ============
export function WeatherEffects() {
  const { condition } = useWeatherStore();

  return (
    <>
      {condition === 'rain' && <Rain />}
      {condition === 'snow' && <Snow />}
      {condition === 'dust' && <DustStorm />}
      {condition === 'storm' && (
        <>
          <Rain />
          <DustStorm />
        </>
      )}
    </>
  );
}
