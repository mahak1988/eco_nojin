/**
 * useEsriTexture Hook
 * ====================
 * Loads Esri World Imagery texture for a given site.
 *
 * Features:
 * - Loads satellite imagery as THREE.Texture
 * - Automatic cleanup on unmount
 * - Handles load errors gracefully
 * - Cross-origin support
 *
 * @module features/hydroma/hooks/useEsriTexture
 */

import { useState, useEffect } from 'react';
import * as THREE from 'three';
import { esriTileUrl } from '../../../lib/demApi';
import type { SiteMeta } from '../types';

// ─────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────

/**
 * Load Esri World Imagery texture for a site
 *
 * @param siteMeta - Site metadata (null = no texture)
 * @returns THREE.Texture or null
 */
export function useEsriTexture(siteMeta: SiteMeta | null): THREE.Texture | null {
  const [texture, setTexture] = useState<THREE.Texture | null>(null);

  useEffect(() => {
    if (!siteMeta) {
      setTexture(null);
      return;
    }

    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin('anonymous');

    const url = esriTileUrl(siteMeta.lat, siteMeta.lon, 14);

    loader.load(
      url,
      (tex) => setTexture(tex),
      undefined,
      () => setTexture(null) // Error handling
    );

    // Cleanup on unmount
    return () => {
      if (texture) {
        texture.dispose();
      }
    };
  }, [siteMeta]);

  return texture;
}
