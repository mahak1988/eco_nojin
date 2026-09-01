import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Beneficial insects: ladybugs, bees, plus pest: locusts
export function InsectsSystem() {
  const groupRef = useRef<THREE.Group>(null);
  
  const insects = useMemo(() => {
    const items = [];
    // Bees (20)
    for (let i = 0; i < 20; i++) {
      items.push({
        type: 'bee',
        color: '#ffcc00',
        size: 0.15,
        phase: Math.random() * Math.PI * 2,
        radius: 5 + Math.random() * 40,
        height: 2 + Math.random() * 5,
        speed: 0.8 + Math.random() * 0.5,
        x: (Math.random() - 0.5) * 60,
        z: (Math.random() - 0.5) * 60,
      });
    }
    // Ladybugs (15) - beneficial
    for (let i = 0; i < 15; i++) {
      items.push({
        type: 'ladybug',
        color: '#d63031',
        size: 0.12,
        phase: Math.random() * Math.PI * 2,
        radius: 3 + Math.random() * 20,
        height: 0.5 + Math.random() * 1,
        speed: 0.3 + Math.random() * 0.3,
        x: (Math.random() - 0.5) * 40,
        z: (Math.random() - 0.5) * 40,
      });
    }
    // Locusts (8) - pests
    for (let i = 0; i < 8; i++) {
      items.push({
        type: 'locust',
        color: '#6c5b3c',
        size: 0.2,
        phase: Math.random() * Math.PI * 2,
        radius: 8 + Math.random() * 30,
        height: 1 + Math.random() * 3,
        speed: 1.2 + Math.random() * 0.8,
        x: (Math.random() - 0.5) * 50,
        z: (Math.random() - 0.5) * 50,
      });
    }
    return items;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((mesh, i) => {
      const ins = insects[i];
      const tt = t * ins.speed + ins.phase;
      mesh.position.set(
        ins.x + Math.sin(tt) * ins.radius,
        ins.height + Math.sin(tt * 2) * 0.5,
        ins.z + Math.cos(tt * 0.7) * ins.radius
      );
      mesh.rotation.y = tt + Math.PI / 2;
    });
  });

  return (
    <group ref={groupRef}>
      {insects.map((ins, i) => (
        <mesh key={i}>
          <sphereGeometry args={[ins.size, 8, 6]} />
          <meshStandardMaterial color={ins.color} />
        </mesh>
      ))}
    </group>
  );
}
