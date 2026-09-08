/** Minimal inline SVG line chart used by the HyDroMa dashboard calculators. */

interface MiniChartProps {
  series: { x: number; y: number }[];
  width?: number;
  height?: number;
  pad?: number;
  yLabel?: string;
  xLabel?: string;
  formatY?: (value: number) => string;
}

export default function MiniChart({
  series,
  width = 480,
  height = 190,
  pad = 30,
  yLabel,
  xLabel,
  formatY = (v: number) => v.toFixed(1),
}: MiniChartProps) {
  const values = series.map((point) => point.y);
  const minY = Math.min(...values);
  const maxY = Math.max(...values);
  const spanY = maxY - minY || 1;
  const minX = series[0]?.x ?? 0;
  const maxX = series[series.length - 1]?.x ?? 1;
  const spanX = maxX - minX || 1;

  const toPx = (point: { x: number; y: number }) => ({
    px: pad + ((point.x - minX) / spanX) * (width - pad * 2),
    py: height - pad - ((point.y - minY) / spanY) * (height - pad * 2),
  });

  const mapped = series.map(toPx);
  const line = mapped.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.px.toFixed(1)} ${p.py.toFixed(1)}`).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img">
      {[0, 0.5, 1].map((fraction) => {
        const y = height - pad - fraction * (height - pad * 2);
        const value = minY + fraction * spanY;
        return (
          <g key={fraction}>
            <line x1={pad} x2={width - pad} y1={y} y2={y} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 5" />
            <text x={pad - 4} y={y + 3} textAnchor="end" fontSize="9" fill="rgba(230,242,234,0.45)">
              {formatY(value)}
            </text>
          </g>
        );
      })}
      <path d={line} fill="none" stroke="#7ee2a8" strokeWidth="2.5" strokeLinecap="round" />
      {mapped.map((p, i) => (
        <circle key={i} cx={p.px} cy={p.py} r="3" fill="#04100b" stroke="#7ee2a8" strokeWidth="1.8" />
      ))}
      {yLabel ? (
        <text x={6} y={14} fontSize="10" fill="rgba(230,242,234,0.5)">
          {yLabel}
        </text>
      ) : null}
      {xLabel ? (
        <text x={width - pad} y={height - 6} textAnchor="end" fontSize="10" fill="rgba(230,242,234,0.5)">
          {xLabel}
        </text>
      ) : null}
    </svg>
  );
}
