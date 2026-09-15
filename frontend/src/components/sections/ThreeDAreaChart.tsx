/** 3D area chart with gradient fill. */
export default function ThreeDAreaChart({
  data,
  onPointClick,
}: {
  data: { label: string; value: number }[];
  onPointClick?: (item: { label: string; value: number }) => void;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);
  const w = 400;
  const h = 200;
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - (d.value / max) * (h - 20);
    return { x, y, ...d };
  });

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const fillD = pathD + ` L ${w} ${h} L 0 ${h} Z`;

  return (
    <div className="chart-3d-container" style={{ perspective: '600px' }}>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ transform: 'rotateX(10deg)' }}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2fb36b" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#2fb36b" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        <path d={fillD} fill="url(#areaGrad)" />
        <path d={pathD} fill="none" stroke="#2fb36b" strokeWidth="2" />
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="4"
            fill="#2fb36b"
            className="cursor-pointer transition-all duration-200 hover:r-6 hover:brightness-125"
            onClick={() => onPointClick?.({ label: p.label, value: p.value })}
          >
            <title>{`${p.label}: ${p.value}`}</title>
          </circle>
        ))}
      </svg>
    </div>
  );
}
