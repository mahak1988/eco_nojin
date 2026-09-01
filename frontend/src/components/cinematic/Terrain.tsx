import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight, TERRAIN_SIZE, perlin } from '../../utils/terrainHeight';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function Terrain() {
  const { condition } = useWeatherStore();
  const SEGMENTS = 256;

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(TERRAIN_SIZE, TERRAIN_SIZE, SEGMENTS, SEGMENTS);
    const pos = geo.attributes.position;
    const colors = new Float32Array(pos.count * 3);

    for (let i = 0; i < pos.count; i++) {
      const px = pos.getX(i);
      const py = pos.getY(i);
      const wx = px;          // world x
      const wz = -py;         // world z after rotateX(-PI/2)
      const h = getTerrainHeight(wx, wz);
      pos.setZ(i, h);

      const nx = wx / TERRAIN_SIZE, nz = wz / TERRAIN_SIZE;
      const var1 = perlin.fbm(nx * 40, nz * 40, 2) * 0.06;
      let r, g, b;

      if (h < -1.8)      { r = 0.16; g = 0.12; b = 0.08; }              // lake bed
      else if (h < -0.6) { r = 0.60 + var1; g = 0.50 + var1; b = 0.33; } // sand shore
      else if (h < 2)    { r = 0.20 + var1; g = 0.47 + var1 * 2; b = 0.14; } // lush grass
      else if (h < 8)    { r = 0.28 + var1; g = 0.52 + var1; b = 0.20; } // grass
      else if (h < 18)   { r = 0.42 + var1; g = 0.40 + var1; b = 0.28; } // dry grass/rock
      else if (h < 30)   { r = 0.47 + var1; g = 0.44 + var1; b = 0.40; } // rock
      else {
        const s = Math.min(1, (h - 30) / 8);
        r = 0.5 + s * 0.42; g = 0.48 + s * 0.45; b = 0.45 + s * 0.5;    // snow
      }
      colors[i * 3] = r; colors[i * 3 + 1] = g; colors[i * 3 + 2] = b;
    }

    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, []);

  const overlay = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#c4a574');
    if (condition === 'snow') return new THREE.Color('#e8e8f0');
    return null;
  }, [condition]);

  return (
    <mesh geometry={geometry} receiveShadow castShadow>
      <meshStandardMaterial
        vertexColors
        roughness={0.88}
        metalness={0.02}
        color={overlay || '#ffffff'}
      />
    </mesh>
  );
}
