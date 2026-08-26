import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky, Stars } from '@react-three/drei';
import * as THREE from 'three';

interface VLLTerrain3DProps {
  interventions: any[];
  weather: { rainfall: number; wind: number; temperature: number; sunIntensity: number };
  activeLayers: Record<string, boolean>;
  timeProgress: number;
  isPlaying: boolean;
}

// ─── Terrain Mesh ─────────────────────────────
const Terrain: React.FC<{ activeLayers: any }> = ({ activeLayers }) => {
  const meshRef = useRef<THREE.Mesh>(null);

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(100, 100, 80, 80);
    const positions = geo.attributes.position;
    
    // DEM: تپه‌ها و آبراهه
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      
      // توپوگرافی اصلی
      let z = Math.sin(x / 20) * Math.cos(y / 20) * 4;
      z += Math.sin(x / 8) * 1.5;
      z += Math.cos(y / 12) * 1.2;
      
      // آبراهه مرکزی (فرورفتگی)
      const streamDistance = Math.abs(y - Math.sin(x / 15) * 3);
      if (streamDistance < 3) {
        z -= (3 - streamDistance) * 0.8;
      }
      
      positions.setZ(i, z);
    }
    
    geo.computeVertexNormals();
    
    // رنگ‌بندی بر اساس لایه فعال
    const colors = [];
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const z = positions.getZ(i);
      
      const color = new THREE.Color();
      
      if (activeLayers.slope) {
        // نقشه شیب (قرمز = پرشیب)
        const slope = Math.abs(Math.sin(x / 20)) + Math.abs(Math.cos(y / 20));
        color.setHSL(0.1 - slope * 0.1, 0.8, 0.5);
      } else if (activeLayers.soil) {
        // نقشه خاک
        const soilType = (Math.sin(x / 10) + Math.cos(y / 10)) / 2;
        color.setHSL(0.08 + soilType * 0.05, 0.5, 0.4);
      } else if (activeLayers.water) {
        // نقشه رطوبت
        const moisture = 0.5 - z / 10 + Math.sin(x / 15) * 0.2;
        color.setHSL(0.55 + moisture * 0.1, 0.7, 0.3 + moisture * 0.3);
      } else if (activeLayers.ndvi) {
        // NDVI (سبز تیره = پررشد)
        const ndvi = 0.3 + z / 10 + Math.sin(x / 8) * 0.2;
        color.setHSL(0.25 + ndvi * 0.05, 0.7, 0.2 + ndvi * 0.3);
      } else {
        // حالت طبیعی
        if (z < -1) color.setHex(0x3a5f8f); // آبراهه
        else if (z < 0) color.setHex(0x8b7355); // خاک مرطوب
        else if (z < 2) color.setHex(0x7da87d); // علف
        else color.setHex(0x5a7a4a); // بوته
      }
      
      colors.push(color.r, color.g, color.b);
    }
    
    geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    return geo;
  }, [activeLayers]);

  return (
    <mesh ref={meshRef} geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <meshStandardMaterial
        vertexColors
        side={THREE.DoubleSide}
        roughness={0.9}
        metalness={0.1}
      />
    </mesh>
  );
};

// ─── Wind Particles ─────────────────────────────
const WindParticles: React.FC<{ wind: number }> = ({ wind }) => {
  const particlesRef = useRef<THREE.InstancedMesh>(null);
  const count = 500;
  
  const particles = useMemo(() => {
    return Array.from({ length: count }, () => ({
      x: (Math.random() - 0.5) * 100,
      y: Math.random() * 20 + 5,
      z: (Math.random() - 0.5) * 100,
      vx: wind * 0.5,
    }));
  }, [wind]);

  useFrame(() => {
    if (!particlesRef.current) return;
    const dummy = new THREE.Object3D();
    
    particles.forEach((p, i) => {
      p.x += p.vx * 0.3;
      p.y += (Math.random() - 0.5) * 0.1;
      
      if (p.x > 50) p.x = -50;
      if (p.y < 2) p.y = 20;
      if (p.y > 25) p.y = 5;
      
      dummy.position.set(p.x, p.y, p.z);
      dummy.scale.setScalar(0.1);
      dummy.updateMatrix();
      particlesRef.current!.setMatrixAt(i, dummy.matrix);
    });
    
    particlesRef.current.instanceMatrix.needsUpdate = true;
  });

  if (wind < 3) return null;

  return (
    <instancedMesh ref={particlesRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[0.1, 4, 4]} />
      <meshBasicMaterial color="#ffffff" transparent opacity={0.4} />
    </instancedMesh>
  );
};

// ─── Rain Drops ─────────────────────────────
const RainDrops: React.FC<{ rainfall: number }> = ({ rainfall }) => {
  const rainRef = useRef<THREE.InstancedMesh>(null);
  const count = Math.min(1000, rainfall * 10);
  
  const drops = useMemo(() => {
    return Array.from({ length: count }, () => ({
      x: (Math.random() - 0.5) * 100,
      y: Math.random() * 30 + 10,
      z: (Math.random() - 0.5) * 100,
      vy: -0.5 - Math.random() * 0.3,
    }));
  }, [count]);

  useFrame(() => {
    if (!rainRef.current) return;
    const dummy = new THREE.Object3D();
    
    drops.forEach((d, i) => {
      d.y += d.vy;
      
      if (d.y < 0) {
        d.y = 30;
        d.x = (Math.random() - 0.5) * 100;
        d.z = (Math.random() - 0.5) * 100;
      }
      
      dummy.position.set(d.x, d.y, d.z);
      dummy.scale.set(0.1, 0.5, 0.1);
      dummy.updateMatrix();
      rainRef.current!.setMatrixAt(i, dummy.matrix);
    });
    
    rainRef.current.instanceMatrix.needsUpdate = true;
  });

  if (rainfall < 5) return null;

  return (
    <instancedMesh ref={rainRef} args={[undefined, undefined, count]}>
      <cylinderGeometry args={[0.05, 0.05, 0.3, 4]} />
      <meshBasicMaterial color="#60a5fa" transparent opacity={0.6} />
    </instancedMesh>
  );
};

// ─── Trees (Windbreaks) ─────────────────────────────
const Tree: React.FC<{ position: [number, number, number]; scale?: number; species?: string }> = ({
  position,
  scale = 1,
  species = 'cypress',
}) => {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (groupRef.current) {
      // انیمیشن باد
      groupRef.current.rotation.z = Math.sin(state.clock.elapsedTime + position[0]) * 0.02;
    }
  });

  const speciesData: Record<string, { trunk: string; leaves: string; height: number }> = {
    cypress: { trunk: '#654321', leaves: '#15803d', height: 8 },
    pine: { trunk: '#654321', leaves: '#166534', height: 10 },
    olive: { trunk: '#8b7355', leaves: '#4d7c0f', height: 5 },
    almond: { trunk: '#a0826d', leaves: '#65a30d', height: 6 },
    oak: { trunk: '#654321', leaves: '#22c55e', height: 7 },
  };
  const data = speciesData[species] || speciesData.cypress;

  return (
    <group ref={groupRef} position={position} scale={scale}>
      {/* تنه */}
      <mesh position={[0, data.height / 2, 0]} castShadow>
        <cylinderGeometry args={[0.3, 0.5, data.height, 8]} />
        <meshStandardMaterial color={data.trunk} roughness={0.9} />
      </mesh>
      {/* تاج */}
      <mesh position={[0, data.height * 0.9, 0]} castShadow>
        <coneGeometry args={[2, data.height * 0.8, 8]} />
        <meshStandardMaterial color={data.leaves} roughness={0.8} />
      </mesh>
    </group>
  );
};

const TreeWindbreak: React.FC<{ intervention: any; terrainHeight: (x: number, z: number) => number }> = ({
  intervention,
  terrainHeight,
}) => {
  const species = intervention.parameters?.species || 'cypress';
  const count = intervention.parameters?.count || 10;
  const rows = intervention.parameters?.rows || 3;
  const startX = intervention.position?.x || 0;
  const startZ = intervention.position?.z || 0;
  
  const trees = [];
  for (let r = 0; r < rows; r++) {
    for (let i = 0; i < count; i++) {
      const x = startX + i * 3;
      const z = startZ + r * 2.5;
      const y = terrainHeight(x, z);
      trees.push(
        <Tree
          key={`tree-${r}-${i}`}
          position={[x, y, z]}
          scale={0.8 + Math.random() * 0.4}
          species={species}
        />
      );
    }
  }
  
  return <>{trees}</>;
};

// ─── Terraces ─────────────────────────────
const Terrace: React.FC<{ intervention: any }> = ({ intervention }) => {
  const count = intervention.parameters?.count || 5;
  const spacing = intervention.parameters?.spacing || 8;
  const startX = intervention.position?.x || -20;
  const startZ = intervention.position?.z || 0;
  
  const terraces = [];
  for (let i = 0; i < count; i++) {
    const z = startZ + i * spacing;
    terraces.push(
      <mesh key={`terrace-${i}`} position={[startX, 0.3, z]} castShadow>
        <boxGeometry args={[40, 0.6, 1.5]} />
        <meshStandardMaterial color="#8b7355" roughness={0.95} />
      </mesh>
    );
  }
  
  return <>{terraces}</>;
};

// ─── Check Dams (بندسار) ─────────────────────────────
const CheckDam: React.FC<{ intervention: any }> = ({ intervention }) => {
  const count = intervention.parameters?.count || 6;
  const startX = intervention.position?.x || 0;
  const startZ = intervention.position?.z || -30;
  
  const dams = [];
  for (let i = 0; i < count; i++) {
    dams.push(
      <mesh
        key={`dam-${i}`}
        position={[startX + Math.sin(i * 0.5) * 5, 0.5, startZ + i * 10]}
        castShadow
      >
        <boxGeometry args={[6, 1.5, 1]} />
        <meshStandardMaterial color="#78716c" roughness={0.9} />
      </mesh>
    );
  }
  
  return <>{dams}</>;
};

// ─── Crops (کشت) ─────────────────────────────
const CropField: React.FC<{ intervention: any; timeProgress: number }> = ({ intervention, timeProgress }) => {
  const growthStage = Math.min(1, timeProgress / 60);
  const count = 20;
  const spacing = 4;
  const startX = intervention.position?.x || -30;
  const startZ = intervention.position?.z || 10;
  
  const crops = [];
  for (let i = 0; i < count; i++) {
    for (let j = 0; j < count; j++) {
      const x = startX + i * spacing;
      const z = startZ + j * spacing;
      const height = growthStage * (1 + Math.random() * 0.3);
      const color = growthStage > 0.7 ? '#fbbf24' : '#84cc16';
      
      crops.push(
        <mesh key={`crop-${i}-${j}`} position={[x, height / 2, z]} castShadow>
          <coneGeometry args={[0.15, height, 6]} />
          <meshStandardMaterial color={color} />
        </mesh>
      );
    }
  }
  
  return <>{crops}</>;
};

// ─── Main Component ─────────────────────────────
export const VLLTerrain3D: React.FC<VLLTerrain3DProps> = ({
  interventions,
  weather,
  activeLayers,
  timeProgress,
}) => {
  // محاسبه ارتفاع زمین در هر نقطه
  const terrainHeight = (x: number, z: number): number => {
    let h = Math.sin(x / 20) * Math.cos(z / 20) * 4;
    h += Math.sin(x / 8) * 1.5;
    h += Math.cos(z / 12) * 1.2;
    const streamDistance = Math.abs(z - Math.sin(x / 15) * 3);
    if (streamDistance < 3) {
      h -= (3 - streamDistance) * 0.8;
    }
    return h;
  };

  const renderIntervention = (intv: any) => {
    switch (intv.id) {
      case 'tree_planting':
      case 'windbreak':
        return <TreeWindbreak key={intv.id} intervention={intv} terrainHeight={terrainHeight} />;
      case 'terrace':
      case 'contour_bunds':
        return <Terrace key={intv.id} intervention={intv} />;
      case 'check_dam':
        return <CheckDam key={intv.id} intervention={intv} />;
      case 'crop_planting':
      case 'cover_crop':
        return <CropField key={intv.id} intervention={intv} timeProgress={timeProgress} />;
      default:
        return null;
    }
  };

  return (
    <Canvas shadows camera={{ position: [40, 30, 40], fov: 50 }}>
      {/* آسمان پویا */}
      <Sky
        sunPosition={[100 * weather.sunIntensity, 50, 100]}
        turbidity={weather.rainfall > 30 ? 20 : 8}
        rayleigh={weather.rainfall > 30 ? 1 : 3}
      />
      
      {/* نور */}
      <ambientLight intensity={0.4 * weather.sunIntensity} />
      <directionalLight
        position={[50, 50, 50]}
        intensity={weather.sunIntensity}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-50}
        shadow-camera-right={50}
        shadow-camera-top={50}
        shadow-camera-bottom={-50}
      />

      {/* Stars اگر شب */}
      {weather.sunIntensity < 0.3 && <Stars radius={100} depth={50} count={5000} />}

      {/* زمین */}
      <Terrain activeLayers={activeLayers} />

      {/* مداخلات */}
      {interventions.map(renderIntervention)}

      {/* آب و هوا */}
      <RainDrops rainfall={weather.rainfall} />
      <WindParticles wind={weather.wind} />

      {/* کنترل دوربین */}
      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        minDistance={20}
        maxDistance={200}
        maxPolarAngle={Math.PI / 2.1}
      />
    </Canvas>
  );
};
