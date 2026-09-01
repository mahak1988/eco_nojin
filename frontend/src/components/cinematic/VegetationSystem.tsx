import { useLayoutEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useQualityStore } from '../../hooks/useQualityStore';

const grassVertex = `
  uniform float uTime;
  uniform float uWindStrength;
  uniform float uGrowthStage;
  attribute float aRandom;
  varying float vHeight;
  varying float vRandom;
  void main() {
    vHeight = position.y;
    vRandom = aRandom;
    vec4 worldPos = instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
    float sway = sin(uTime * 2.0 + worldPos.x * 0.35 + aRandom * 6.28) * position.y * position.y * uWindStrength;
    float swayZ = cos(uTime * 1.7 + worldPos.z * 0.35 + aRandom * 6.28) * position.y * position.y * uWindStrength * 0.6;
    vec3 displaced = position;
    displaced.x += sway;
    displaced.z += swayZ;
    displaced.y *= (0.3 + uGrowthStage * 0.7);
    vec4 mvPosition = modelViewMatrix * instanceMatrix * vec4(displaced, 1.0);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const grassFragment = `
  uniform vec3 uBaseColor;
  uniform vec3 uTipColor;
  varying float vHeight;
  varying float vRandom;
  void main() {
    vec3 color = mix(uBaseColor, uTipColor, clamp(vHeight, 0.0, 1.0));
    color *= 0.85 + vRandom * 0.3;
    gl_FragColor = vec4(color, 1.0);
  }
`;

export function VegetationSystem() {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const { windSpeed, condition, plantGrowthStage } = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);

  // Adaptive grass density
  const target = tier === 'high' ? 8000 : tier === 'medium' ? 4500 : 2500;

  const blade = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const v = new Float32Array([-0.05, 0, 0, 0.05, 0, 0, 0.03, 0.5, 0, -0.03, 0.5, 0, 0, 1, 0]);
    const idx = new Uint16Array([0, 1, 2, 0, 2, 3, 3, 2, 4]);
    g.setAttribute('position', new THREE.BufferAttribute(v, 3));
    g.setIndex(new THREE.BufferAttribute(idx, 1));
    g.computeVertexNormals();
    return g;
  }, []);

  const { transforms, rands } = useMemo(() => {
    const list: { x: number; y: number; z: number; rot: number; scale: number }[] = [];
    const r: number[] = [];
    let guard = 0;
    while (list.length < target && guard < target * 4) {
      guard++;
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.sqrt(Math.random()) * 110;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = getTerrainHeight(x, z);
      if (y < -1.0) continue; // no grass under water
      list.push({ x, y, z, rot: Math.random() * Math.PI, scale: 0.7 + Math.random() * 0.9 });
      r.push(Math.random());
    }
    return { transforms: list, rands: new Float32Array(r) };
  }, [target]);

  // FIX: useLayoutEffect (useMemo ran before ref existed -> matrices never applied)
  useLayoutEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) return;
    const dummy = new THREE.Object3D();
    transforms.forEach((t, i) => {
      dummy.position.set(t.x, t.y - 0.05, t.z);
      dummy.rotation.set(0, t.rot, 0);
      dummy.scale.setScalar(t.scale);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
  }, [transforms]);

  const baseColor = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#8b6f47');
    if (condition === 'snow') return new THREE.Color('#d4d4dc');
    return new THREE.Color('#2d5a3d');
  }, [condition]);

  const tipColor = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#a0845a');
    if (condition === 'snow') return new THREE.Color('#ffffff');
    return new THREE.Color('#3d7a4f').lerp(new THREE.Color('#7cb342'), plantGrowthStage);
  }, [condition, plantGrowthStage]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      materialRef.current.uniforms.uWindStrength.value = windSpeed * 0.02;
      materialRef.current.uniforms.uGrowthStage.value = plantGrowthStage;
      materialRef.current.uniforms.uBaseColor.value = baseColor;
      materialRef.current.uniforms.uTipColor.value = tipColor;
    }
  });

  const count = transforms.length;

  return (
    <instancedMesh key={count} ref={meshRef} args={[blade, undefined, count]} castShadow={tier === 'high'}>
      <shaderMaterial
        ref={materialRef}
        vertexShader={grassVertex}
        fragmentShader={grassFragment}
        uniforms={{
          uTime: { value: 0 },
          uWindStrength: { value: 0.3 },
          uGrowthStage: { value: 0.5 },
          uBaseColor: { value: baseColor },
          uTipColor: { value: tipColor },
        }}
        side={THREE.DoubleSide}
      />
      <instancedBufferAttribute attach="attributes-aRandom" args={[rands, 1]} />
    </instancedMesh>
  );
}
