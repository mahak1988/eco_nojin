import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulatorStore } from '../simulatorStore';

/**
 * Procedural clouds: overlapping low-poly spheres that drift with wind.
 * Zero external textures - immune to network failures.
 */
function Cloud({ position, color, scale = 1 }: {
  position: [number, number, number];
  color: string;
  scale?: number;
}) {
  const puffs = [
    { pos: [0, 0, 0], s: 10 },
    { pos: [8, 1.5, -1], s: 8 },
    { pos: [-9, 0.8, 2], s: 9 },
    { pos: [3, -1.5, 5], s: 7 },
    { pos: [-5, 2, -4], s: 8 },
  ];

  return (
    <group position={position}>
      {puffs.map((p, i) => (
        <mesh key={i} position={[p.pos[0] * scale, p.pos[1] * scale, p.pos[2] * scale]}>
          <icosahedronGeometry args={[p.s * scale, 1]} />
          <meshStandardMaterial
            color={color}
            transparent
            opacity={0.82}
            roughness={1}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  );
}

export function Clouds() {
  const { weather, windSpeed } = useSimulatorStore();
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (!groupRef.current) return;
    groupRef.current.position.x += delta * (1.5 + windSpeed * 0.15);
    if (groupRef.current.position.x > 300) groupRef.current.position.x = -300;
  });

  const color = (() => {
    if (weather === 'storm') return '#4a5568';
    if (weather === 'dust') return '#a08055';
    if (weather === 'rain') return '#8a9aa8';
    return '#ffffff';
  })();

  const count = weather === 'clear' ? 3 : weather === 'storm' ? 6 : 4;

  return (
    <group ref={groupRef}>
      {Array.from({ length: count }).map((_, i) => (
        <Cloud
          key={i}
          position={[(i - count / 2) * 80, 90 + (i % 3) * 15, -150 + (i % 2) * 40]}
          color={color}
          scale={1.2 + (i % 3) * 0.3}
        />
      ))}
    </group>
  );
}
