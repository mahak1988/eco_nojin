import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function Birds() {
  const count = 12;
  const groupRef = useRef<THREE.Group>(null);

  const birds = useMemo(() => {
    return new Array(count).fill(0).map((_, i) => ({
      angle: (i / count) * Math.PI * 2,
      radius: 40 + Math.random() * 20,
      height: 30 + Math.random() * 15,
      speed: 0.3 + Math.random() * 0.2,
      offset: Math.random() * Math.PI * 2,
    }));
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((bird, i) => {
      const b = birds[i];
      const angle = b.angle + t * b.speed;
      bird.position.set(
        Math.cos(angle) * b.radius,
        b.height + Math.sin(t * 2 + b.offset) * 2,
        Math.sin(angle) * b.radius
      );
      bird.rotation.y = -angle - Math.PI / 2;
      bird.rotation.z = Math.sin(t * 8 + b.offset) * 0.3;
    });
  });

  return (
    <group ref={groupRef}>
      {birds.map((_, i) => (
        <mesh key={i}>
          <coneGeometry args={[0.5, 1.5, 4]} />
          <meshStandardMaterial color="#2d3436" />
        </mesh>
      ))}
    </group>
  );
}
