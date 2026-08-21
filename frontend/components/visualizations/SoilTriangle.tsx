"use client";
import { useTheme } from '../../lib/theme-context';
import { useI18n } from '../../lib/i18n-context';

interface Props { clay: number; silt: number; sand: number; }

// USDA soil texture triangle vertices (simplified)
// Top = 100% clay, bottom-left = 100% sand, bottom-right = 100% silt
export default function SoilTriangle({ clay, silt, sand }: Props) {
  const { t } = useI18n();
  const { colors } = useTheme();
  const total = clay + silt + sand || 1;
  const c = (clay / total) * 100;
  const si = (silt / total) * 100;
  const sa = (sand / total) * 100;

  // Convert ternary to Cartesian (equilateral triangle)
  const W_SIZE = 400;
  const H = W_SIZE * Math.sqrt(3) / 2;
  const A = { x: W_SIZE / 2, y: 10 };        // Top (100% clay)
  const B = { x: 10, y: H + 10 };            // Bottom-left (100% sand)
  const C = { x: W_SIZE - 10, y: H + 10 };   // Bottom-right (100% silt)

  // Point calculation: weighted average
  const px = (c * A.x + sa * B.x + si * C.x) / 100;
  const py = (c * A.y + sa * B.y + si * C.y) / 100;

  // Texture zones (simplified)
  const zones = [
    { name: 'Clay', path: `${A.x},${A.y} ${A.x-50},${A.y+86} ${A.x+50},${A.y+86}`, fill: colors.danger + '30' },
    { name: 'Sandy', path: `${B.x},${B.y} ${B.x+180},${B.y} ${B.x+90},${B.y-156}`, fill: colors.warm + '30' },
    { name: 'Silty', path: `${C.x},${C.y} ${C.x-180},${C.y} ${C.x-90},${C.y-156}`, fill: colors.accent + '30' },
    { name: 'Loam', path: `${W_SIZE/2-70},${H-50} ${W_SIZE/2+70},${H-50} ${W_SIZE/2+40},${H-120} ${W_SIZE/2-40},${H-120}`, fill: colors.success + '40' },
  ];

  return (
    <div style={{ textAlign: 'center' }}>
      <svg viewBox={`0 0 ${W_SIZE} ${H + 20}`} style={{ maxWidth: '100%', height: 'auto' }}>
        {/* Zones */}
        {zones.map((z, i) => (
          <polygon key={i} points={z.path} fill={z.fill} stroke={colors.border} strokeWidth="1" />
        ))}

        {/* Triangle outline */}
        <polygon
          points={`${A.x},${A.y} ${B.x},${B.y} ${C.x},${C.y}`}
          fill="none" stroke={colors.text} strokeWidth="2"
        />

        {/* Grid lines (every 20%) */}
        {[20, 40, 60, 80].map(p => {
          const t = p / 100;
          return (
            <g key={p} opacity="0.2" stroke={colors.textMuted} strokeWidth="0.5">
              <line x1={A.x + (B.x-A.x)*t} y1={A.y + (B.y-A.y)*t}
                    x2={A.x + (C.x-A.x)*t} y2={A.y + (C.y-A.y)*t} />
              <line x1={B.x + (C.x-B.x)*t} y1={B.y + (C.y-B.y)*t}
                    x2={B.x + (A.x-B.x)*t} y2={B.y + (A.y-B.y)*t} />
              <line x1={C.x + (A.x-C.x)*t} y1={C.y + (A.y-C.y)*t}
                    x2={C.x + (B.x-C.x)*t} y2={C.y + (B.y-C.y)*t} />
            </g>
          );
        })}

        {/* Current point */}
        <circle cx={px} cy={py} r="8" fill={colors.primary} stroke="white" strokeWidth="2" />
        <circle cx={px} cy={py} r="12" fill="none" stroke={colors.primary} strokeWidth="1" opacity="0.5" />

        {/* Labels */}
        <text x={A.x} y={A.y - 5} textAnchor="middle" fill={colors.text} fontSize="12" fontWeight="bold">{t('soil_field_clay')} {c.toFixed(0)}%</text>
        <text x={B.x} y={B.y + 15} textAnchor="start" fill={colors.text} fontSize="12" fontWeight="bold">{t('soil_field_sand')} {sa.toFixed(0)}%</text>
        <text x={C.x} y={C.y + 15} textAnchor="end" fill={colors.text} fontSize="12" fontWeight="bold">{t('soil_field_silt')} {si.toFixed(0)}%</text>
      </svg>
    </div>
  );
}
