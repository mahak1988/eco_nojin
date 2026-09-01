import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Traditional water well with visible water level
export function WellSystem() {
  const waterRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (waterRef.current) {
      const t = state.clock.elapsedTime;
      const mat = waterRef.current.material as THREE.MeshStandardMaterial;
      // Gentle wave on water surface
      waterRef.current.position.y = -1 + Math.sin(t * 2) * 0.02;
    }
  });

  return (
    <group position={[35, 0, -35]}>
      {/* Stone well wall */}
      <mesh castShadow>
        <cylinderGeometry args={[1.5, 1.8, 1.5, 16, 1, true]} />
        <meshStandardMaterial color="#8b7355" roughness={0.95} side={THREE.DoubleSide} />
      </mesh>
      {/* Top rim */}
      <mesh position={[0, 0.8, 0]} castShadow>
        <torusGeometry args={[1.6, 0.15, 8, 24]} />
        <meshStandardMaterial color="#6b5d47" roughness={0.8} />
      </mesh>
      {/* Water inside */}
      <mesh ref={waterRef} position={[0, -1, 0]}>
        <cylinderGeometry args={[1.4, 1.4, 0.1, 24]} />
        <meshStandardMaterial color="#2a5a8a" metalness={0.3} roughness={0.1} />
      </mesh>
      {/* Wooden cover frame */}
      <mesh position={[0, 2, 0]} castShadow>
        <boxGeometry args={[0.2, 3, 0.2]} />
        <meshStandardMaterial color="#5a3a20" />
      </mesh>
      <mesh position={[0, 3.5, 0]} castShadow>
        <boxGeometry args={[3, 0.2, 0.2]} />
        <meshStandardMaterial color="#5a3a20" />
      </mesh>
      {/* Bucket rope */}
      <mesh position={[0, 2.5, 0]}>
        <cylinderGeometry args={[0.02, 0.02, 2, 6]} />
        <meshStandardMaterial color="#8b6914" />
      </mesh>
    </group>
  );
}
