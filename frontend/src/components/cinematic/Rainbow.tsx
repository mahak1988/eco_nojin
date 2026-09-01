import { useMemo } from 'react';
import * as THREE from 'three';

const rainbowColors = ['#ff0000', '#ff7f00', '#ffff00', '#00ff00', '#0000ff', '#4b0082', '#9400d3'];

export function Rainbow() {
  const arcs = useMemo(() => {
    return rainbowColors.map((color, i) => {
      const radius = 60 + i * 1.5;
      const curve = new THREE.EllipseCurve(0, 0, radius, radius, 0, Math.PI, false, 0);
      const points = curve.getPoints(60);
      const geometry = new THREE.BufferGeometry().setFromPoints(
        points.map((p) => new THREE.Vector3(p.x, p.y, 0))
      );
      return { geometry, color, key: i };
    });
  }, []);

  return (
    <group position={[0, 5, -80]} rotation={[0, 0, 0]}>
      {arcs.map(({ geometry, color, key }) => (
        <primitive
          key={key}
          object={new THREE.Line(
            geometry,
            new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.5, linewidth: 3 })
          )}
        />
      ))}
    </group>
  );
}
