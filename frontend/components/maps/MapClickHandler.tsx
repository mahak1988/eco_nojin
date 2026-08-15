"use client";
import { useEffect, useRef } from 'react';

interface MapClickHandlerProps {
  onClick: (lat: number, lon: number) => void;
}

export default function MapClickHandler({ onClick }: MapClickHandlerProps) {
  const onClickRef = useRef(onClick);
  onClickRef.current = onClick;

  useEffect(() => {
    let cleanupFn: (() => void) | undefined;
    const interval = setInterval(() => {
      const container = document.querySelector('.leaflet-container') as any;
      if (!container || !container._leaflet_id) return;
      clearInterval(interval);
      const L = (window as any).L;
      if (!L || !L._maps) return;
      const maps = Object.values(L._maps) as any[];
      const map = maps[0];
      if (!map) return;
      const handleClick = (e: any) => {
        if (e.latlng) onClickRef.current(e.latlng.lat, e.latlng.lng);
      };
      map.on('click', handleClick);
      cleanupFn = () => map.off('click', handleClick);
    }, 100);
    return () => {
      clearInterval(interval);
      cleanupFn?.();
    };
  }, []);

  return null;
}
