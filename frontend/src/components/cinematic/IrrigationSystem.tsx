import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Sprinkler irrigation with rotating water spray
function Sprinkler({ position }: { position: [number, number, number] }) {
  const sprayRef = useRef<THREE.Points>(null);
  const count = 300;
  
  const positions = useMemo(() => new Float32Array(count * 3), []);
  const velocities = useMemo(() => {
    const v = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      v[i * 3] = Math.cos(angle) * 0.3;
      v[i * 3 + 1] = 0.4 + Math.random() * 0.2;
      v[i * 3 + 2] = Math.sin(angle) * 0.3;
    }
    return v;
  }, []);

  useFrame((state) => {
    if (!sprayRef.current) return;
    const posAttr = sprayRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const t = state.clock.elapsedTime;
    
    for (let i = 0; i < count; i++) {
      arr[i * 3] += velocities[i * 3] * 0.15;
      arr[i * 3 + 1] += velocities[i * 3 + 1] * 0.1 - 0.015;
      arr[i * 3 + 2] += velocities[i * 3 + 2] * 0.15;
      
      if (arr[i * 3 + 1] < 0) {
        const angle = (i / count) * Math.PI * 2 + t * 2;
        const speed = 0.3 + Math.random() * 0.3;
        arr[i * 3] = 0;
        arr[i * 3 + 1] = 2;
        arr[i * 3 + 2] = 0;
        velocities[i * 3] = Math.cos(angle) * speed;
        velocities[i * 3 + 2] = Math.sin(angle) * speed;
      }
    }
    posAttr.needsUpdate = true;
  });

  return (
    <group position={position}>
      {/* Sprinkler post */}
      <mesh position={[0, 1, 0]} castShadow>
        <cylinderGeometry args={[0.08, 0.1, 2, 8]} />
        <meshStandardMaterial color="#2c3e50" metalness={0.8} />
      </mesh>
      <mesh position={[0, 2.1, 0]}>
        <sphereGeometry args={[0.15, 8, 6]} />
        <meshStandardMaterial color="#34495e" metalness={0.9} />
      </mesh>
      {/* Water spray */}
      <points ref={sprayRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
        </bufferGeometry>
        <pointsMaterial
          size={0.1}
          color="#4fa3d1"
          transparent
          opacity={0.7}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}

export function IrrigationSystem() {
  // Place 6 sprinklers across the field
  const sprinklerPositions: [number, number, number][] = [
    [-20, 0, -20], [0, 0, -20], [20, 0, -20],
    [-20, 0, 0], [0, 0, 0], [20, 0, 0],
  ];
  
  return (
    <group>
      {sprinklerPositions.map((pos, i) => (
        <Sprinkler key={i} position={pos} />
      ))}
      {/* Drip irrigation pipes */}
      {[10, 20, 30].map((z) => (
        <mesh key={z} position={[0, 0.1, z]} rotation={[0, 0, 0]}>
          <cylinderGeometry args={[0.05, 0.05, 80, 8]} />
          <meshStandardMaterial color="#1e3a5f" />
        </mesh>
      ))}
    </group>
  );
}
