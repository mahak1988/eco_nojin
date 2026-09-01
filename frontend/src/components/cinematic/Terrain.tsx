import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function Terrain() {
  const meshRef = useRef<THREE.Mesh>(null);
  const { condition, plantGrowthStage } = useWeatherStore();

  // Generate procedural heightmap
  const { geometry, position } = useMemo(() => {
    const size = 200;
    const segments = 128;
    const geo = new THREE.PlaneGeometry(size, size, segments, segments);
    const posAttr = geo.attributes.position;
    const posArray = new Float32Array(posAttr.count);
    
    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getY(i);
      // Multi-octave noise for natural terrain
      const h =
        Math.sin(x * 0.05) * Math.cos(z * 0.05) * 3 +
        Math.sin(x * 0.12 + 1.3) * Math.cos(z * 0.08) * 1.5 +
        Math.sin(x * 0.3) * Math.cos(z * 0.25) * 0.4;
      posAttr.setZ(i, h);
      posArray[i] = h;
    }
    geo.computeVertexNormals();
    return { geometry: geo, position: posArray };
  }, []);

  // Dynamic color based on weather and growth
  const color = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#8b6f47');
    if (condition === 'snow') return new THREE.Color('#e8e8f0');
    const green = new THREE.Color('#3a7d44').lerp(
      new THREE.Color('#6ba368'),
      plantGrowthStage
    );
    return green;
  }, [condition, plantGrowthStage]);

  return (
    <mesh ref={meshRef} geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <meshStandardMaterial
        color={color}
        roughness={0.9}
        metalness={0.05}
        flatShading={false}
      />
    </mesh>
  );
}
