import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// Custom shader for wind-driven grass sway
const grassVertexShader = `
  uniform float uTime;
  uniform float uWindStrength;
  uniform float uGrowthStage;
  attribute vec3 offset;
  attribute float random;
  varying float vHeight;
  varying vec3 vNormal;
  
  void main() {
    vHeight = position.y;
    vNormal = normalMatrix * normal;
    
    // Wind sway based on height and wind strength
    float swayAmount = position.y * position.y * uWindStrength * 0.1;
    float sway = sin(uTime * 2.0 + offset.x * 0.5 + random * 6.28) * swayAmount;
    float swayZ = cos(uTime * 1.7 + offset.z * 0.5 + random * 6.28) * swayAmount * 0.5;
    
    vec3 displaced = position;
    displaced.x += sway;
    displaced.z += swayZ;
    displaced.y *= uGrowthStage;
    
    vec4 worldPos = instanceMatrix * vec4(displaced, 1.0);
    vec4 mvPosition = modelViewMatrix * worldPos;
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const grassFragmentShader = `
  uniform vec3 uBaseColor;
  uniform vec3 uTipColor;
  varying float vHeight;
  varying vec3 vNormal;
  
  void main() {
    vec3 color = mix(uBaseColor, uTipColor, vHeight);
    
    // Simple lighting
    vec3 lightDir = normalize(vec3(0.5, 1.0, 0.3));
    float diffuse = max(dot(vNormal, lightDir), 0.0);
    color *= 0.6 + diffuse * 0.6;
    
    gl_FragColor = vec4(color, 1.0);
  }
`;

export function VegetationSystem() {
  const grassCount = 8000;
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  
  const { windSpeed, condition, plantGrowthStage } = useWeatherStore();

  // Generate grass blade geometry
  const bladeGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const vertices = new Float32Array([
      -0.05, 0, 0,
       0.05, 0, 0,
       0.03, 0.5, 0,
      -0.03, 0.5, 0,
       0, 1, 0,
    ]);
    const indices = new Uint16Array([0,1,2, 0,2,3, 3,2,4]);
    geo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    geo.setIndex(new THREE.BufferAttribute(indices, 1));
    geo.computeVertexNormals();
    return geo;
  }, []);

  // Instance matrices and random attributes
  const { dummy, offsets, randoms } = useMemo(() => {
    const dummy = new THREE.Object3D();
    const offsets = new Float32Array(grassCount * 3);
    const randoms = new Float32Array(grassCount);
    
    for (let i = 0; i < grassCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.sqrt(Math.random()) * 80;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = Math.sin(x * 0.05) * Math.cos(z * 0.05) * 3;
      
      dummy.position.set(x, y, z);
      dummy.rotation.y = Math.random() * Math.PI;
      const scale = 0.8 + Math.random() * 0.8;
      dummy.scale.set(scale, scale, scale);
      dummy.updateMatrix();
      
      offsets[i * 3] = x;
      offsets[i * 3 + 1] = y;
      offsets[i * 3 + 2] = z;
      randoms[i] = Math.random();
    }
    
    return { dummy, offsets, randoms };
  }, []);

  // Apply instance matrices
  useMemo(() => {
    if (!meshRef.current) return;
    const dummy = new THREE.Object3D();
    for (let i = 0; i < grassCount; i++) {
      const x = offsets[i * 3];
      const y = offsets[i * 3 + 1];
      const z = offsets[i * 3 + 2];
      dummy.position.set(x, y, z);
      dummy.rotation.y = randoms[i] * Math.PI;
      const scale = 0.8 + randoms[i] * 0.8;
      dummy.scale.set(scale, scale, scale);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
  }, [offsets, randoms]);

  // Colors based on weather condition
  const baseColor = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#8b6f47');
    if (condition === 'snow') return new THREE.Color('#d4d4dc');
    return new THREE.Color('#2d5a3d');
  }, [condition]);

  const tipColor = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#a0845a');
    if (condition === 'snow') return new THREE.Color('#ffffff');
    const growth = plantGrowthStage;
    return new THREE.Color('#3d7a4f').lerp(new THREE.Color('#7cb342'), growth);
  }, [condition, plantGrowthStage]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      materialRef.current.uniforms.uWindStrength.value = windSpeed * 0.02;
      materialRef.current.uniforms.uGrowthStage.value = 0.3 + plantGrowthStage * 0.7;
      materialRef.current.uniforms.uBaseColor.value = baseColor;
      materialRef.current.uniforms.uTipColor.value = tipColor;
    }
  });

  return (
    <instancedMesh ref={meshRef} args={[bladeGeometry, undefined, grassCount]} castShadow>
      <shaderMaterial
        ref={materialRef}
        vertexShader={grassVertexShader}
        fragmentShader={grassFragmentShader}
        uniforms={{
          uTime: { value: 0 },
          uWindStrength: { value: 0.3 },
          uGrowthStage: { value: 0.5 },
          uBaseColor: { value: baseColor },
          uTipColor: { value: tipColor },
        }}
        side={THREE.DoubleSide}
      />
    </instancedMesh>
  );
}
