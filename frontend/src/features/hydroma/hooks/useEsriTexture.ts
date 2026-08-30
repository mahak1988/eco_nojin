/**
 * useEsriTexture Hook
 * ====================
 * Loads Esri World Imagery texture for a given site.
 *
 * @module features/hydroma/hooks/useEsriTexture
 */

import { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { esriTileUrl } from '../../../lib/demApi';
import type { SiteMeta } from '../types';

export function useEsriTexture(siteMeta: SiteMeta | null): THREE.Texture | null {
  const [texture, setTexture] = useState<THREE.Texture | null>(null);
  const textureRef = useRef<THREE.Texture | null>(null);

  useEffect(() => {
    if (!siteMeta) {
      setTexture(null);
      textureRef.current = null;
      return;
    }

    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin('anonymous');

    const url = esriTileUrl(siteMeta.lat, siteMeta.lon, 14);

    loader.load(
      url,
      (tex) => {
        textureRef.current = tex;
        setTexture(tex);
      },
      undefined,
      () => {
        textureRef.current = null;
        setTexture(null);
      }
    );

    return () => {
      if (textureRef.current) {
        textureRef.current.dispose();
        textureRef.current = null;
      }
    };
  }, [siteMeta]);

  return texture;
}
