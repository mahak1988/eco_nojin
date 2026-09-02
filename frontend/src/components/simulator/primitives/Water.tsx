import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulatorStore } from '../simulatorStore';

/**
 * Procedural lake: circle geometry + wavy shoreline + animated shader.
 * Zero external textures.
 */
export function Water() {
  const { weather, timeOfDay } = useSimulatorStore();
  const matRef = useRef<THREE.ShaderMaterial>(null);

  const baseColor = useMemo(() => {
    if (weather === 'dust') return '#a0826b';
    if (weather === 'storm') return '#4a5568';
    if (timeOfDay === 'dawn') return '#e08a5f';
    if (timeOfDay === 'dusk') return '#c85878';
    if (timeOfDay === 'night') return '#1a2a4a';
    return '#3a7ac0';
  }, [weather, timeOfDay]);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(baseColor) },
  }), []);

  useFrame((state) => {
    if (matRef.current) {
      matRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      matRef.current.uniforms.uColor.value.lerp(new THREE.Color(baseColor), 0.05);
    }
  });

  return (
    <mesh position={[0, -0.8, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <circleGeometry args={[45, 64]} />
      <shaderMaterial
        ref={matRef}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        vertexShader={`
          uniform float uTime;
          varying vec2 vUv;
          varying float vWave;
          void main() {
            vUv = uv;
            vec3 p = position;
            p.z = sin(p.x * 0.3 + uTime * 1.5) * 0.15
                + cos(p.y * 0.25 + uTime * 1.2) * 0.1;
            vWave = p.z;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
          }
        `}
        fragmentShader={`
          uniform vec3 uColor;
          uniform float uTime;
          varying vec2 vUv;
          varying float vWave;
          void main() {
            float r = length(vUv - 0.5) * 2.0;
            float wob = sin(vUv.x * 32.0 + uTime * 0.5) * 0.04
                      + cos(vUv.y * 28.0 - uTime * 0.4) * 0.04;
            float shore = smoothstep(1.0 + wob, 0.88 + wob, r);
            if (shore < 0.01) discard;

            vec3 deep = uColor * 0.6;
            vec3 shallow = uColor * 1.2;
            vec3 col = mix(deep, shallow, 1.0 - smoothstep(0.3, 0.95, r));

            // highlights
            float spec = pow(max(sin(vUv.x * 50.0 + uTime * 1.2)
                               * sin(vUv.y * 45.0 - uTime * 0.9), 0.0), 8.0);
            col += vec3(0.9, 0.95, 1.0) * spec * 0.3;

            gl_FragColor = vec4(col, 0.88 * shore);
          }
        `}
      />
    </mesh>
  );
}
