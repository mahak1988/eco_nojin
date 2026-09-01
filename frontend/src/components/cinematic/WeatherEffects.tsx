import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// ============ RAIN SYSTEM ============
function Rain() {
  const { intensity, windSpeed, windDirection } = useWeatherStore();
  const count = 5000;
  const meshRef = useRef<THREE.Points>(null);

  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 200;
      pos[i * 3 + 1] = Math.random() * 80 + 20;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 200;
      vel[i * 3 + 1] = -1.5 - Math.random() * 0.5;
    }
    return [pos, vel];
  }, []);

  useFrame(() => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const windX = Math.cos((windDirection * Math.PI) / 180) * windSpeed * 0.01;
    const windZ = Math.sin((windDirection * Math.PI) / 180) * windSpeed * 0.01;
    
    for (let i = 0; i < count; i++) {
      arr[i * 3] += windX;
      arr[i * 3 + 1] += velocities[i * 3 + 1];
      arr[i * 3 + 2] += windZ;
      
      if (arr[i * 3 + 1] < 0) {
        arr[i * 3] = (Math.random() - 0.5) * 200;
        arr[i * 3 + 1] = Math.random() * 20 + 80;
        arr[i * 3 + 2] = (Math.random() - 0.5) * 200;
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
        size={0.15}
        color="#a0c4ff"
        transparent
        opacity={0.6 * intensity}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

// ============ SNOW SYSTEM ============
function Snow() {
  const { intensity, windSpeed } = useWeatherStore();
  const count = 3000;
  const meshRef = useRef<THREE.Points>(null);
  const offsets = useMemo(() => new Float32Array(count).map(() => Math.random() * Math.PI * 2), []);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 200;
      pos[i * 3 + 1] = Math.random() * 80 + 20;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 200;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const t = state.clock.elapsedTime;
    
    for (let i = 0; i < count; i++) {
      arr[i * 3] += Math.sin(t + offsets[i]) * 0.02 + windSpeed * 0.002;
      arr[i * 3 + 1] -= 0.15;
      arr[i * 3 + 2] += Math.cos(t + offsets[i]) * 0.02;
      
      if (arr[i * 3 + 1] < 0) {
        arr[i * 3] = (Math.random() - 0.5) * 200;
        arr[i * 3 + 1] = 80;
        arr[i * 3 + 2] = (Math.random() - 0.5) * 200;
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
        size={0.3}
        color="#ffffff"
        transparent
        opacity={0.9 * intensity}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

// ============ DUST STORM ============
function DustStorm() {
  const { intensity, windSpeed } = useWeatherStore();
  const count = 4000;
  const meshRef = useRef<THREE.Points>(null);
  const offsets = useMemo(() => new Float32Array(count).map(() => Math.random() * 1000), []);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 200;
      pos[i * 3 + 1] = Math.random() * 40;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 200;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const t = state.clock.elapsedTime;
    
    for (let i = 0; i < count; i++) {
      const off = offsets[i];
      arr[i * 3] += (windSpeed * 0.05 + Math.sin(t * 0.5 + off) * 0.3);
      arr[i * 3 + 1] += Math.sin(t + off) * 0.1;
      arr[i * 3 + 2] += Math.cos(t * 0.7 + off) * 0.2;
      
      if (arr[i * 3] > 100) arr[i * 3] = -100;
      if (arr[i * 3] < -100) arr[i * 3] = 100;
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
        color="#c9a66b"
        transparent
        opacity={0.5 * intensity}
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
