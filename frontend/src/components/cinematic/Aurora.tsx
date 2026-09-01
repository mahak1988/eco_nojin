import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const auroraVertex = `
  varying vec2 vUv;
  varying vec3 vPos;
  uniform float uTime;
  void main() {
    vUv = uv;
    vec3 p = position;
    p.y += sin(p.x * 0.05 + uTime * 0.5) * 3.0;
    p.y += cos(p.z * 0.08 + uTime * 0.3) * 2.0;
    vPos = p;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }
`;

const auroraFragment = `
  varying vec2 vUv;
  varying vec3 vPos;
  uniform float uTime;
  uniform float uIntensity;

  vec3 auroraColor(float t) {
    vec3 green = vec3(0.1, 0.9, 0.4);
    vec3 teal = vec3(0.1, 0.7, 0.8);
    vec3 purple = vec3(0.5, 0.2, 0.9);
    vec3 pink = vec3(0.9, 0.3, 0.6);
    if (t < 0.33) return mix(green, teal, t / 0.33);
    if (t < 0.66) return mix(teal, purple, (t - 0.33) / 0.33);
    return mix(purple, pink, (t - 0.66) / 0.34);
  }

  void main() {
    float wave = sin(vUv.x * 10.0 + uTime) * 0.5 + 0.5;
    float wave2 = cos(vUv.x * 7.0 - uTime * 0.7) * 0.5 + 0.5;
    float bands = wave * wave2;
    float fade = smoothstep(0.0, 0.3, vUv.y) * smoothstep(1.0, 0.5, vUv.y);
    vec3 color = auroraColor(vUv.x + sin(uTime * 0.2) * 0.3);
    float alpha = bands * fade * uIntensity;
    gl_FragColor = vec4(color, alpha * 0.6);
  }
`;

export function Aurora() {
  const matRef = useRef<THREE.ShaderMaterial>(null);

  const geometry = useMemo(() => new THREE.PlaneGeometry(300, 60, 64, 16), []);

  useFrame((state) => {
    if (matRef.current) {
      matRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh geometry={geometry} position={[0, 80, -120]}>
      <shaderMaterial
        ref={matRef}
        vertexShader={auroraVertex}
        fragmentShader={auroraFragment}
        uniforms={{
          uTime: { value: 0 },
          uIntensity: { value: 1.0 },
        }}
        transparent
        side={THREE.DoubleSide}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
}
