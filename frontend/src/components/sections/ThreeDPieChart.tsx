/** 3D donut/pie chart with click interaction. */
export default function ThreeDPieChart({
  data,
  onSegmentClick,
}: {
  data: { label: string; value: number; color: string }[];
  onSegmentClick?: (item: { label: string; value: number }) => void;
}) {
  const total = data.reduce((s, d) => s + d.value, 0);
  let cumulative = 0;
  const segments = data.map((d) => {
    const start = cumulative / total;
    cumulative += d.value;
    const end = cumulative / total;
    return { ...d, start, end };
  });

  const describeArc = (cx: number, cy: number, r: number, startAngle: number, endAngle: number) => {
    const start = { x: cx + r * Math.cos(startAngle * Math.PI - Math.PI / 2), y: cy + r * Math.sin(startAngle * Math.PI - Math.PI / 2) };
    const end = { x: cx + r * Math.cos(endAngle * Math.PI - Math.PI / 2), y: cy + r * Math.sin(endAngle * Math.PI - Math.PI / 2) };
    const largeArc = endAngle - startAngle > 0.5 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
  };

  return (
    <div className="chart-3d-container donut-3d" style={{ perspective: '800px' }}>
      <svg viewBox="0 0 200 200" className="w-full max-h-[280px]" role="img" aria-label="Chart">
        {segments.map((seg) => (
          <path
            key={seg.label}
            d={describeArc(100, 100, 80, seg.start * 360, seg.end * 360)}
            fill="none"
            stroke={seg.color}
            strokeWidth="30"
            strokeLinecap="butt"
            className="transition-all duration-300 hover:brightness-125 cursor-pointer"
            onClick={() => onSegmentClick?.(seg)}
          />
        ))}
        <circle cx="100" cy="100" r="40" fill="var(--color-night-900)" />
      </svg>
    </div>
  );
}
