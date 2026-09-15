/** Radial progress chart with 3D effect. */
export default function RadialProgressChart({
  value,
  max = 100,
  size = 120,
  label,
}: {
  value: number;
  max?: number;
  size?: number;
  label?: string;
}) {
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(value / max, 1);
  const offset = circumference * (1 - progress);

  return (
    <div className="relative" style={{ width: size, height: size }} dir="ltr">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full" style={{ transform: 'rotateX(30deg)' }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-leaf-500)"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
          style={{ filter: 'drop-shadow(0 0 6px rgba(47,179,107,0.4))' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-extrabold text-[var(--color-leaf-300)]">{Math.round(progress * 100)}%</span>
        {label && <span className="text-[10px] text-[var(--color-night-200)]/50">{label}</span>}
      </div>
    </div>
  );
}
