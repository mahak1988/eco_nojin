'use client';
import { useEffect, useRef, useState } from 'react';
import Globe from 'react-globe.gl';

interface GlobePoint {
  lat: number;
  lng: number;
  label?: string;
}

interface GlobeMapProps {
  points?: GlobePoint[];
  height?: number;
  width?: number | string;
}

export default function GlobeMap({ 
  points = [], // آرایه‌ای از نقاط { lat: 35.6892, lng: 51.3890, label: 'Farm A' }
  height = 400,
  width = '100%',
}: GlobeMapProps) {
  const globeRef = useRef<any>(null);
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
    if (globeRef.current) {
      // تنظیم اتوماتیک چرخش کره
      globeRef.current.controls().autoRotate = true;
      globeRef.current.controls().autoRotateSpeed = 0.5;
    }
  }, []);

  if (!hasMounted) return null;

  return (
    <div className="rounded-xl overflow-hidden border border-border bg-card">
      <Globe
        ref={globeRef}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        // رنگ‌بندی بر اساس تم داشبورد
        atmosphereColor="var(--color-primary)"
        atmosphereAltitude={0.15}
        lineHoverPrecision={1}
        // نشانگرهای روی کره
        pointsData={points}
        pointColor={() => 'var(--color-accent)'}
        pointAltitude={0.05}
        pointRadius={0.25}
        pointsMerge={false}
        pointLabel={(d: any) => `<div style="color: white; font-weight: bold;">${d.label}</div>`}
        height={height}
        width={width as any}
      />
    </div>
  );
}