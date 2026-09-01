import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const butterflyColors = ['#ff6b9d', '#feca57', '#48dbfb', '#ff9ff3', '#f368e0'];

export function Butterflies() {
  const count = 15;
  const groupRef = useRef<THREE.Group>(null);

  const flies = useMemo(() => {
    return new Array(count).fill(0).map(() => ({
      x: (Math.random() - 0.5) * 80,
      z: (Math.random() - 0.5) * 80,
      speed: 0.5 + Math.random() * 0.5,
      phase: Math.random() * Math.PI * 2,
      color: butterflyColors[Math.floor(Math.random() * butterflyColors.length)],
    }));
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((bfly, i) => {
      const f = flies[i];
      bfly.position.set(
        f.x + Math.sin(t * f.speed + f.phase) * 5,
        2 + Math.sin(t * 2 + f.phase) * 1.5,
        f.z + Math.cos(t * f.speed * 0.7 + f.phase) * 5
      );
      bfly.rotation.y = t * f.speed;
      bfly.scale.setScalar(1 + Math.sin(t * 10 + f.phase) * 0.2);
    });
  });

  return (
    <group ref={groupRef}>
      {flies.map((f, i) => (
        <mesh key={i}>
          <planeGeometry args={[0.8, 0.6]} />
          <meshBasicMaterial color={f.color} side={THREE.DoubleSide} transparent opacity={0.9} />
        </mesh>
      ))}
    </group>
  );
}
