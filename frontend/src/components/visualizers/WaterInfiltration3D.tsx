import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

interface WaterInfiltration3DProps {
  soilTexture?: 'sand' | 'loam' | 'clay';
  rainfallIntensity?: number;
  showLayers?: boolean;
}

const SoilLayer = ({
  y,
  height,
  color,
  opacity = 1,
}: {
  y: number;
  height: number;
  color: string;
  opacity?: number;
}) => (
  <mesh position={[0, y, 0]}>
    <boxGeometry args={[4, height, 4]} />
    <meshStandardMaterial color={color} transparent opacity={opacity} roughness={0.9} />
  </mesh>
);

const RainDrops = ({ intensity }: { intensity: number }) => {
  const dropsRef = useRef<THREE.InstancedMesh>(null);
  const dropsData = useMemo(() => {
    return Array.from({ length: 200 }, () => ({
      x: (Math.random() - 0.5) * 4,
      y: 5 + Math.random() * 3,
      z: (Math.random() - 0.5) * 4,
      vy: -0.1 - Math.random() * 0.1,
      active: Math.random() < intensity / 100,
    }));
  }, [intensity]);

  useFrame(() => {
    if (!dropsRef.current) return;
    const dummy = new THREE.Object3D();
    dropsData.forEach((drop, i) => {
      if (!drop.active) return;
      drop.y += drop.vy;
      if (drop.y <= 1.5) {
        drop.y = 5 + Math.random() * 3;
        drop.x = (Math.random() - 0.5) * 4;
        drop.z = (Math.random() - 0.5) * 4;
      }
      dummy.position.set(drop.x, drop.y, drop.z);
      dummy.updateMatrix();
      dropsRef.current!.setMatrixAt(i, dummy.matrix);
    });
    dropsRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={dropsRef} args={[undefined, undefined, 200]}>
      <cylinderGeometry args={[0.02, 0.02, 0.3, 4]} />
      <meshStandardMaterial color="#4a90e2" transparent opacity={0.6} />
    </instancedMesh>
  );
};

const InfiltratingWater = ({ soilAbsorption }: { soilAbsorption: number }) => {
  const particlesRef = useRef<THREE.InstancedMesh>(null);
  const particles = useMemo(() => {
    return Array.from({ length: 100 }, () => ({
      x: (Math.random() - 0.5) * 3.5,
      y: 1.5 - Math.random() * 3,
      z: (Math.random() - 0.5) * 3.5,
      vy: -0.02 * soilAbsorption,
    }));
  }, [soilAbsorption]);

  useFrame(() => {
    if (!particlesRef.current) return;
    const dummy = new THREE.Object3D();
    particles.forEach((p, i) => {
      p.y += p.vy;
      if (p.y < -2) {
        p.y = 1.5;
        p.x = (Math.random() - 0.5) * 3.5;
        p.z = (Math.random() - 0.5) * 3.5;
      }
      dummy.position.set(p.x, p.y, p.z);
      dummy.scale.setScalar(0.8 + Math.random() * 0.4);
      dummy.updateMatrix();
      particlesRef.current!.setMatrixAt(i, dummy.matrix);
    });
    particlesRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={particlesRef} args={[undefined, undefined, 100]}>
      <sphereGeometry args={[0.08, 8, 8]} />
      <meshStandardMaterial
        color="#1e90ff"
        transparent
        opacity={0.7}
        emissive="#1e90ff"
        emissiveIntensity={0.3}
      />
    </instancedMesh>
  );
};

export const WaterInfiltration3D: React.FC<WaterInfiltration3DProps> = ({
  soilTexture = 'loam',
  rainfallIntensity = 30,
  showLayers = true,
}) => {
  const soilProperties = {
    sand: { absorption: 1.5, color: '#d4a574' },
    loam: { absorption: 1.0, color: '#8b7355' },
    clay: { absorption: 0.3, color: '#5a4632' },
  };
  const soil = soilProperties[soilTexture];

  return (
    <div
      style={{
        width: '100%',
        height: 500,
        background: '#1a1a2e',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
      }}
    >
      <Canvas camera={{ position: [6, 4, 6], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 10, 5]} intensity={1} castShadow />

        <SoilLayer y={1} height={1} color="#2d5016" opacity={showLayers ? 0.8 : 1} />
        <SoilLayer y={0} height={1} color={soil.color} opacity={showLayers ? 0.7 : 1} />
        <SoilLayer y={-1} height={1} color="#654321" opacity={showLayers ? 0.6 : 1} />
        <SoilLayer y={-2} height={1} color="#3e2723" opacity={showLayers ? 0.5 : 1} />

        <RainDrops intensity={rainfallIntensity} />
        <InfiltratingWater soilAbsorption={soil.absorption} />

        <OrbitControls enablePan enableZoom enableRotate />
      </Canvas>
    </div>
  );
};
