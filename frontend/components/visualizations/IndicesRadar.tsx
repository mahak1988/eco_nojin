"use client";
import { useTheme } from '../../lib/theme-context';

interface Props {
  ndvi: number; evi: number; savi: number; ndwi: number; nbr: number;
}

export default function IndicesRadar({ ndvi, evi, savi, ndwi, nbr }: Props) {
  const { colors } = useTheme();
  const size = 300;
  const center = size / 2;
  const radius = 110;

  // Normalize indices to 0-1 range (assume -1 to 1 typical range)
  const normalize = (v: number) => Math.max(0, Math.min(1, (v + 1) / 2));
  const values = [
    { name: 'NDVI', value: normalize(ndvi), raw: ndvi },
    { name: 'EVI', value: normalize(evi), raw: evi },
    { name: 'SAVI', value: normalize(savi), raw: savi },
    { name: 'NDWI', value: normalize(ndwi), raw: ndwi },
    { name: 'NBR', value: normalize(nbr), raw: nbr },
  ];

  const n = values.length;
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (i: number, r: number) => ({
    x: center + r * Math.cos(i * angleStep - Math.PI / 2),
    y: center + r * Math.sin(i * angleStep - Math.PI / 2),
  });

  const polygonPoints = values.map((v, i) => {
    const p = getPoint(i, radius * v.value);
    return `${p.x},${p.y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${size} ${size}`} style={{ maxWidth: '100%', height: 'auto' }}>
      {/* Grid circles */}
      {[0.25, 0.5, 0.75, 1].map(scale => (
        <circle key={scale} cx={center} cy={center} r={radius * scale}
          fill="none" stroke={colors.border} strokeWidth="1" opacity="0.3" />
      ))}

      {/* Axis lines */}
      {values.map((_, i) => {
        const p = getPoint(i, radius);
        return <line key={i} x1={center} y1={center} x2={p.x} y2={p.y}
          stroke={colors.border} strokeWidth="1" opacity="0.3" />;
      })}

      {/* Data polygon */}
      <polygon points={polygonPoints}
        fill={`${colors.primary}40`} stroke={colors.primary} strokeWidth="2" />

      {/* Data points */}
      {values.map((v, i) => {
        const p = getPoint(i, radius * v.value);
        return <circle key={i} cx={p.x} cy={p.y} r="5"
          fill={colors.primary} stroke="white" strokeWidth="2" />;
      })}

      {/* Labels */}
      {values.map((v, i) => {
        const p = getPoint(i, radius + 25);
        return (
          <g key={i}>
            <text x={p.x} y={p.y - 5} textAnchor="middle"
              fill={colors.text} fontSize="12" fontWeight="700">
              {v.name}
            </text>
            <text x={p.x} y={p.y + 10} textAnchor="middle"
              fill={colors.primary} fontSize="11" fontWeight="600">
              {v.raw.toFixed(2)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
