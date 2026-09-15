import { useState, useEffect, useRef } from 'react';

/** Enhanced interactive map with markers. */
export default function InteractiveMapWidget({
  height = 300,
}: {
  height?: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredMarker, setHoveredMarker] = useState<string | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const markers = [
    { name: 'مشهد', x: 70, y: 35, type: 'forest' },
    { name: 'انزلی', x: 55, y: 30, type: 'wetland' },
    { name: 'اصفهان', x: 60, y: 50, type: 'agriculture' },
    { name: 'تبریز', x: 40, y: 25, type: 'forest' },
    { name: 'رشت', x: 50, y: 32, type: 'wetland' },
  ];

  const typeColors: Record<string, string> = { forest: '#2fb36b', wetland: '#2a9bb5', agriculture: '#d49b3f' };

  useEffect(() => {
    const timer = setTimeout(() => setMapLoaded(true), 1500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      ref={containerRef}
      className="rounded-3xl glass overflow-hidden relative"
      style={{ height }}
    >
      {!mapLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-[var(--color-night-900)]">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-leaf-500)]/25 border-t-leaf-400" aria-hidden />
        </div>
      )}
      <div className="absolute inset-0 data-stream-bg">
        <svg className="w-full h-full" aria-hidden>
          {markers.map((m) => (
            <g key={m.name}>
              <circle
                cx={`${m.x}%`}
                cy={`${m.y}%`}
                r="8"
                fill={typeColors[m.type]}
                opacity="0.3"
                className="animate-pulse-soft"
              />
              <circle
                cx={`${m.x}%`}
                cy={`${m.y}%`}
                r="4"
                fill={typeColors[m.type]}
                className="cursor-pointer transition-transform hover:scale-150"
                onMouseEnter={() => setHoveredMarker(m.name)}
                onMouseLeave={() => setHoveredMarker(null)}
              />
              {hoveredMarker === m.name && (
                <text
                  x={`${m.x}%`}
                  y={`${m.y - 5}%`}
                  textAnchor="middle"
                  fill="#eaf6ee"
                  fontSize="10"
                  fontWeight="bold"
                >
                  {m.name}
                </text>
              )}
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}
