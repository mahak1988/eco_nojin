import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Cinematic opening: camera glides from a high aerial shot
 * down to the farm view over ~5 seconds (easeOutCubic),
 * then hands control to the user (OrbitControls enabled).
 */
export function CameraIntro({ onDone }: { onDone: () => void }) {
  const { camera } = useThree();
  const st = useRef({ t: 0, done: false });
  const start = useMemo(() => new THREE.Vector3(430, 260, 430), []);
  const end = useMemo(() => new THREE.Vector3(120, 60, 120), []);

  useEffect(() => {
    camera.position.copy(start);
    camera.lookAt(0, 0, 0);
  }, [camera, start]);

  useFrame((_, delta) => {
    const s = st.current;
    if (s.done) return;
    s.t += delta / 5; // 5 second glide
    const k = Math.min(1, s.t);
    const e = 1 - Math.pow(1 - k, 3); // easeOutCubic
    camera.position.lerpVectors(start, end, e);
    camera.lookAt(0, 0, 0);
    if (k >= 1) {
      s.done = true;
      onDone();
    }
  });

  return null;
}
