/**
 * Geolocation Hook with offline caching
 *
 * Uses deferred client state pattern to avoid hydration mismatches.
 */
import { useState, useEffect, useCallback } from 'react';

interface GeoPosition {
  latitude: number;
  longitude: number;
  accuracy: number;
  altitude: number | null;
  timestamp: number;
}

const CACHE_KEY = 'eco-nojin-last-position';
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export function useGeolocation() {
  const [position, setPosition] = useState<GeoPosition | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isCached, setIsCached] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Mark as mounted only after client hydration
  useEffect(() => {
    setMounted(true);

    // Load cached position on mount
    if (typeof localStorage === 'undefined') return;

    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const parsed: GeoPosition = JSON.parse(cached);
        if (Date.now() - parsed.timestamp < CACHE_TTL) {
          setPosition(parsed);
          setIsCached(true);
        }
      }
    } catch {
      // Ignore cache errors
    }
  }, []);

  const getCurrentPosition = useCallback(async (): Promise<GeoPosition | null> => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setError('Geolocation not supported');
      return null;
    }

    setLoading(true);
    setError(null);

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const geoPos: GeoPosition = {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            altitude: pos.coords.altitude,
            timestamp: Date.now(),
          };

          setPosition(geoPos);
          setIsCached(false);
          setLoading(false);

          try {
            localStorage.setItem(CACHE_KEY, JSON.stringify(geoPos));
          } catch {
            // Ignore
          }

          resolve(geoPos);
        },
        (err) => {
          setError(err.message);
          setLoading(false);

          // Fallback to cached position
          try {
            const cached = localStorage.getItem(CACHE_KEY);
            if (cached) {
              const parsed: GeoPosition = JSON.parse(cached);
              setPosition(parsed);
              setIsCached(true);
              resolve(parsed);
            } else {
              resolve(null);
            }
          } catch {
            resolve(null);
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: CACHE_TTL,
        }
      );
    });
  }, []);

  return {
    position,
    error,
    loading,
    isCached,
    mounted,
    getCurrentPosition,
  };
}
