import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface AnimalProps {
  type: 'cattle' | 'sheep' | 'goat' | 'poultry';
  position: [number, number, number];
}

/**
 * مدل سه‌بعدی ساده حیوان (placeholder - در production از GLB استفاده می‌شود)
 */
const Animal: React.FC<AnimalProps> = ({ type, position }) => {
  const groupRef = useRef<THREE.Group>(null);
  const offset = useRef(Math.random() * Math.PI * 2);

  useFrame((state) => {
    if (groupRef.current) {
      const t = state.clock.elapsedTime + offset.current;
      // حرکت آرام
      groupRef.current.position.x = position[0] + Math.sin(t * 0.3) * 2;
      groupRef.current.position.z = position[2] + Math.cos(t * 0.3) * 2;
      groupRef.current.rotation.y = Math.atan2(Math.cos(t * 0.3) * 2, -Math.sin(t * 0.3) * 2);
    }
  });

  const config = {
    cattle: { body: [1.5, 1, 2.5], legs: 0.8, color: '#6b4423' },
    sheep: { body: [0.7, 0.6, 1.2], legs: 0.4, color: '#f0f0e8' },
    goat: { body: [0.6, 0.5, 1.1], legs: 0.5, color: '#a0826d' },
    poultry: { body: [0.2, 0.3, 0.3], legs: 0.2, color: '#c0392b' },
  }[type];

  return (
    <group ref={groupRef} position={position}>
      {/* بدن */}
      <mesh position={[0, config.legs + config.body[1] / 2, 0]} castShadow>
        <boxGeometry args={config.body as [number, number, number]} />
        <meshStandardMaterial color={config.color} />
      </mesh>
      {/* سر */}
      <mesh position={[0, config.legs + config.body[1], config.body[2] / 2]} castShadow>
        <sphereGeometry args={[config.body[1] * 0.6, 12, 12]} />
        <meshStandardMaterial color={config.color} />
      </mesh>
      {/* ۴ پا */}
      {[
        [-config.body[0] / 2.5, config.legs / 2, -config.body[2] / 2.5],
        [config.body[0] / 2.5, config.legs / 2, -config.body[2] / 2.5],
        [-config.body[0] / 2.5, config.legs / 2, config.body[2] / 2.5],
        [config.body[0] / 2.5, config.legs / 2, config.body[2] / 2.5],
      ].map((pos, i) => (
        <mesh key={i} position={pos as [number, number, number]} castShadow>
          <cylinderGeometry args={[0.08, 0.08, config.legs, 6]} />
          <meshStandardMaterial color="#2c2c2c" />
        </mesh>
      ))}
    </group>
  );
};

interface AnimalHerdProps {
  herd: {
    type: 'cattle' | 'sheep' | 'goat' | 'poultry';
    count: number;
  };
  areaSize?: number;
}

export const AnimalHerd: React.FC<AnimalHerdProps> = ({ herd, areaSize = 40 }) => {
  const positions: [number, number, number][] = [];
  for (let i = 0; i < Math.min(herd.count, 50); i++) {
    positions.push([(Math.random() - 0.5) * areaSize, 0, (Math.random() - 0.5) * areaSize]);
  }

  return (
    <group>
      {positions.map((pos, i) => (
        <Animal key={i} type={herd.type} position={pos} />
      ))}
    </group>
  );
};
