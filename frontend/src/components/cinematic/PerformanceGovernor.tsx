import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useQualityStore } from '../../hooks/useQualityStore';

/**
 * FPS Governor: measures real FPS every 2.5s and shifts the quality tier.
 * Keeps the 3D simulator as fluid as the 2D homepage on ANY GPU.
 *
 *  - FPS < 27  -> downgrade (high->medium->low)
 *  - FPS > 55  -> upgrade   (low->medium->high)
 */
export function PerformanceGovernor() {
  const tier = useQualityStore((s) => s.tier);
  const setTier = useQualityStore((s) => s.setTier);
  const acc = useRef({ frames: 0, last: performance.now() });

  useFrame(() => {
    const a = acc.current;
    a.frames += 1;
    const now = performance.now();
    const dt = now - a.last;
    if (dt >= 2500) {
      const fps = (a.frames * 1000) / dt;
      a.frames = 0;
      a.last = now;
      if (fps < 27 && tier !== 'low') {
        setTier(tier === 'high' ? 'medium' : 'low');
      } else if (fps > 55 && tier !== 'high') {
        setTier(tier === 'low' ? 'medium' : 'high');
      }
    }
  });

  return null;
}
