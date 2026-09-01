import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Flowing river with animated shader
export function RiverSystem() {
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  
  const geometry = useMemo(() => {
    // Create a curved river path
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-100, 0.3, -40),
      new THREE.Vector3(-60, 0.3, -30),
      new THREE.Vector3(-20, 0.3, -35),
      new THREE.Vector3(20, 0.3, -25),
      new THREE.Vector3(60, 0.3, -30),
      new THREE.Vector3(100, 0.3, -45),
    ]);
    const points = curve.getPoints(50);
    const shape = new THREE.Shape();
    shape.moveTo(-3, 0);
    shape.lineTo(3, 0);
    const geo = new THREE.ExtrudeGeometry(shape, {
      steps: 50,
      extrudePath: curve,
      bevelEnabled: false,
    });
    return geo;
  }, []);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh geometry={geometry}>
      <shaderMaterial
        ref={materialRef}
        uniforms={{
          uTime: { value: 0 },
        }}
        transparent
        vertexShader={`
          varying vec2 vUv;
          void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `}
        fragmentShader={`
          uniform float uTime;
          varying vec2 vUv;
          void main() {
            float flow = fract(vUv.x * 5.0 - uTime * 0.5);
            vec3 deep = vec3(0.1, 0.3, 0.5);
            vec3 shallow = vec3(0.3, 0.6, 0.8);
            vec3 foam = vec3(0.9, 0.95, 1.0);
            vec3 color = mix(deep, shallow, flow);
            float edgeFoam = smoothstep(0.0, 0.1, abs(vUv.y - 0.5)) * smoothstep(0.5, 0.45, abs(vUv.y - 0.5));
            color = mix(color, foam, edgeFoam * 0.5);
            gl_FragColor = vec4(color, 0.85);
          }
        `}
      />
    </mesh>
  );
}
