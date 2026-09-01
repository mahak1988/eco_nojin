import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Ocean shoreline with wave dynamics
export function Coastline() {
  const waterRef = useRef<THREE.Mesh>(null);
  const foamRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (waterRef.current) {
      const geo = waterRef.current.geometry as THREE.PlaneGeometry;
      const pos = geo.attributes.position;
      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i);
        const z = pos.getY(i);
        const h = Math.sin(x * 0.1 + t) * 0.3 + Math.sin(z * 0.15 + t * 0.7) * 0.2;
        pos.setZ(i, h);
      }
      pos.needsUpdate = true;
    }
    if (foamRef.current) {
      foamRef.current.position.x = Math.sin(t * 0.5) * 2 - 85;
    }
  });

  return (
    <group position={[-90, 0.2, 0]}>
      {/* Ocean water */}
      <mesh ref={waterRef} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[30, 150, 32, 64]} />
        <meshStandardMaterial
          color="#0a4a7a"
          metalness={0.4}
          roughness={0.3}
          transparent
          opacity={0.9}
        />
      </mesh>
      {/* Sandy beach */}
      <mesh position={[15, -0.1, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[20, 150]} />
        <meshStandardMaterial color="#e8d5a6" roughness={0.95} />
      </mesh>
      {/* Foam line */}
      <mesh ref={foamRef} position={[0, 0.15, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[2, 150]} />
        <meshBasicMaterial color="#ffffff" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}
