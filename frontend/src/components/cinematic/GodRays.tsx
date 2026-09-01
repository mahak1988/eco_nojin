import { useMemo } from 'react';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function GodRays() {
  const { sunPosition, timeOfDay } = useWeatherStore();

  const rays = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 0.5 - Math.PI * 0.25;
      arr.push({
        position: [
          sunPosition[0] * 0.5 + Math.cos(angle) * 10,
          sunPosition[1] * 0.5,
          sunPosition[2] * 0.5 + Math.sin(angle) * 10,
        ] as [number, number, number],
        rotation: [0.3 + i * 0.05, angle, 0] as [number, number, number],
      });
    }
    return arr;
  }, [sunPosition]);

  const intensity = timeOfDay === 'day' ? 0.15 : timeOfDay === 'dawn' || timeOfDay === 'dusk' ? 0.25 : 0;

  return (
    <group>
      {rays.map((ray, i) => (
        <mesh key={i} position={ray.position} rotation={ray.rotation}>
          <cylinderGeometry args={[0.5, 3, 80, 8, 1, true]} />
          <meshBasicMaterial
            color="#fff8dc"
            transparent
            opacity={intensity}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  );
}
