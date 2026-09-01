import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function Poultry() {
  const groupRef = useRef<THREE.Group>(null);
  
  const birds = useMemo(() => {
    const list = [];
    // Chickens (12)
    for (let i = 0; i < 12; i++) {
      list.push({
        color: i % 3 === 0 ? '#8b4513' : i % 3 === 1 ? '#ffffff' : '#d4a574',
        size: 0.4,
        x: -10 + Math.random() * 20,
        z: 20 + Math.random() * 15,
        phase: Math.random() * Math.PI * 2,
        speed: 0.2 + Math.random() * 0.2,
      });
    }
    // Ducks (5)
    for (let i = 0; i < 5; i++) {
      list.push({
        color: '#f4d03f',
        size: 0.35,
        x: -40 + Math.random() * 10,
        z: -15 + Math.random() * 10,
        phase: Math.random() * Math.PI * 2,
        speed: 0.15 + Math.random() * 0.15,
      });
    }
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((g, i) => {
      const b = birds[i];
      const tt = t * b.speed + b.phase;
      g.position.set(
        b.x + Math.sin(tt) * 3,
        Math.abs(Math.sin(tt * 4)) * 0.2,
        b.z + Math.cos(tt * 0.8) * 3
      );
      g.rotation.y = tt * 0.5;
    });
  });

  return (
    <group ref={groupRef}>
      {birds.map((b, i) => (
        <group key={i} scale={b.size}>
          <mesh position={[0, 0.4, 0]} castShadow>
            <sphereGeometry args={[0.5, 8, 6]} />
            <meshStandardMaterial color={b.color} />
          </mesh>
          <mesh position={[0.3, 0.7, 0]} castShadow>
            <sphereGeometry args={[0.25, 8, 6]} />
            <meshStandardMaterial color={b.color} />
          </mesh>
          {/* Beak */}
          <mesh position={[0.55, 0.7, 0]}>
            <coneGeometry args={[0.08, 0.15, 4]} />
            <meshStandardMaterial color="#ff6b00" />
          </mesh>
        </group>
      ))}
    </group>
  );
}
