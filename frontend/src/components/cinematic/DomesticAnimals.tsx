import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Low-poly farm animals: cows, sheep, horses
function Animal({ type, color, size = 1 }: { type: string; color: string; size?: number }) {
  return (
    <group scale={size}>
      {/* Body */}
      <mesh position={[0, size * 0.8, 0]} castShadow>
        <boxGeometry args={[1.5, 0.8, 0.7]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {/* Head */}
      <mesh position={[0.8, size * 1.1, 0]} castShadow>
        <boxGeometry args={[0.5, 0.5, 0.5]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {/* Legs */}
      {[[-0.5, 0, -0.2], [-0.5, 0, 0.2], [0.5, 0, -0.2], [0.5, 0, 0.2]].map((pos, i) => (
        <mesh key={i} position={pos as [number, number, number]} castShadow>
          <boxGeometry args={[0.15, 0.8, 0.15]} />
          <meshStandardMaterial color="#2d3436" />
        </mesh>
      ))}
    </group>
  );
}

export function DomesticAnimals() {
  const groupRef = useRef<THREE.Group>(null);
  
  const animals = useMemo(() => {
    const list = [];
    // Cows (5)
    for (let i = 0; i < 5; i++) {
      list.push({
        type: 'cow',
        color: i % 2 === 0 ? '#ffffff' : '#8b4513',
        size: 1.2,
        x: 20 + Math.random() * 30,
        z: -20 + Math.random() * 30,
        speed: 0.05 + Math.random() * 0.05,
        phase: Math.random() * Math.PI * 2,
      });
    }
    // Sheep (8)
    for (let i = 0; i < 8; i++) {
      list.push({
        type: 'sheep',
        color: '#f5f5dc',
        size: 0.8,
        x: -30 + Math.random() * 25,
        z: 10 + Math.random() * 30,
        speed: 0.08 + Math.random() * 0.05,
        phase: Math.random() * Math.PI * 2,
      });
    }
    // Horses (3)
    for (let i = 0; i < 3; i++) {
      list.push({
        type: 'horse',
        color: '#6b3e2a',
        size: 1.5,
        x: 40 + Math.random() * 20,
        z: 20 + Math.random() * 20,
        speed: 0.1 + Math.random() * 0.1,
        phase: Math.random() * Math.PI * 2,
      });
    }
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((g, i) => {
      const a = animals[i];
      const tt = t * a.speed + a.phase;
      g.position.set(
        a.x + Math.sin(tt) * 8,
        0,
        a.z + Math.cos(tt * 0.8) * 8
      );
      g.rotation.y = tt + Math.PI / 2;
    });
  });

  return (
    <group ref={groupRef}>
      {animals.map((a, i) => (
        <group key={i}>
          <Animal type={a.type} color={a.color} size={a.size} />
        </group>
      ))}
    </group>
  );
}
