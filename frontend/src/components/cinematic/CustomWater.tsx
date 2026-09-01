import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface Props {
  position?: [number, number, number];
  radius?: number;
  color?: string;
  waveHeight?: number;
  waveSpeed?: number;
  segments?: number;
}

/**
 * Organic lake: circular geometry + noise-wobbled shoreline alpha.
 * No more square water plane!
 */
export function CustomWater({
  position = [0, 0, 0],
  radius = 55,
  color = '#2a5a8a',
  waveHeight = 0.15,
  waveSpeed = 0.5,
  segments = 96,
}: Props) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(color) },
    uWaveHeight: { value: waveHeight },
    uWaveSpeed: { value: waveSpeed },
  }), [color, waveHeight, waveSpeed]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, 0]}>
      <circleGeometry args={[radius, segments]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        side={THREE.DoubleSide}
        vertexShader={`
          uniform float uTime;
          uniform float uWaveHeight;
          uniform float uWaveSpeed;
          varying vec2 vUv;
          varying float vWave;
          void main() {
            vUv = uv;
            vec3 p = position;
            float t = uTime * uWaveSpeed;
            float w1 = sin(p.x * 0.25 + t * 1.6) * cos(p.y * 0.2 + t * 1.1);
            float w2 = sin((p.x + p.y) * 0.5 + t * 2.2) * 0.4;
            p.z = (w1 + w2) * uWaveHeight;
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
            // radial distance from lake center (0..1 at rim)
            float r = length(vUv - 0.5) * 2.0;

            // wobble the shoreline so it looks natural, not circular-perfect
            float wob = sin(vUv.x * 34.0 + uTime * 0.4) * 0.03
                      + cos(vUv.y * 29.0 - uTime * 0.3) * 0.03;
            float shore = smoothstep(1.0 + wob, 0.86 + wob, r);
            if (shore < 0.01) discard;

            // depth gradient: deep center -> shallow rim
            vec3 deep = uColor * 0.55;
            vec3 shallow = uColor * 1.35;
            vec3 col = mix(shallow, deep, smoothstep(0.3, 0.9, r) * -1.0 + 1.0);
            col = mix(deep, shallow, 1.0 - smoothstep(0.2, 0.95, r));

            // moving highlights
            float spec = pow(max(sin(vUv.x * 60.0 + uTime * 1.4) * sin(vUv.y * 55.0 - uTime * 1.1), 0.0), 6.0);
            col += vec3(0.9, 0.95, 1.0) * spec * 0.25;

            // foam near shore
            float foam = smoothstep(0.9, 0.99, r + wob) * 0.6;
            col = mix(col, vec3(0.92, 0.97, 1.0), foam);

            gl_FragColor = vec4(col, 0.9 * shore);
          }
        `}
      />
    </mesh>
  );
}

export default CustomWater;
