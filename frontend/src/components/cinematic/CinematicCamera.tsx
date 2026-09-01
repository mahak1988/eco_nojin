import { useFrame, useThree } from '@react-three/fiber';
import { useArtisticStore } from '../../hooks/useArtisticStore';

export function CinematicCamera() {
  const { camera } = useThree();
  const enableCinematicCamera = useArtisticStore((s) => s.enableCinematicCamera);

  useFrame((state) => {
    if (!enableCinematicCamera) return;
    const t = state.clock.elapsedTime * 0.1;
    const radius = 50;
    camera.position.x = Math.cos(t) * radius;
    camera.position.z = Math.sin(t) * radius;
    camera.position.y = 20 + Math.sin(t * 0.5) * 5;
    camera.lookAt(0, 5, 0);
  });

  return null;
}
