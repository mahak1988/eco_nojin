import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function Lightning() {
  const lightRef = useRef<THREE.PointLight>(null);
  const boltRef = useRef<THREE.Line>(null);
  const [flash, setFlash] = useState(0);
  const nextStrike = useRef(Math.random() * 3 + 2);

  const createBolt = () => {
    const points: THREE.Vector3[] = [];
    let x = (Math.random() - 0.5) * 80;
    let y = 90;
    let z = (Math.random() - 0.5) * 80 - 40;
    points.push(new THREE.Vector3(x, y, z));
    while (y > 5) {
      x += (Math.random() - 0.5) * 12;
      y -= 8 + Math.random() * 6;
      z += (Math.random() - 0.5) * 12;
      points.push(new THREE.Vector3(x, Math.max(y, 2), z));
    }
    return points;
  };

  const [boltPoints, setBoltPoints] = useState<THREE.Vector3[]>(createBolt);

  useFrame((state, delta) => {
    nextStrike.current -= delta;
    if (nextStrike.current <= 0) {
      setFlash(1);
      setBoltPoints(createBolt());
      nextStrike.current = Math.random() * 4 + 2;
    }
    if (flash > 0) {
      const newFlash = Math.max(0, flash - delta * 4);
      setFlash(newFlash);
      if (lightRef.current) lightRef.current.intensity = newFlash * 500;
      if (boltRef.current) {
        const mat = boltRef.current.material as THREE.LineBasicMaterial;
        mat.opacity = newFlash;
      }
    }
  });

  const geometry = new THREE.BufferGeometry().setFromPoints(boltPoints);

  return (
    <>
      <pointLight ref={lightRef} position={[0, 80, -40]} intensity={0} color="#cfe8ff" distance={300} />
      <primitive
        ref={boltRef}
        object={new THREE.Line(
          geometry,
          new THREE.LineBasicMaterial({ color: '#e8f4ff', transparent: true, opacity: 0, linewidth: 2 })
        )}
      />
    </>
  );
}
