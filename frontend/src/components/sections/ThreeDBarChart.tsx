/** 3D interactive bar chart with click-to-expand. */
export default function ThreeDBarChart({
  data,
  onBarClick,
}: {
  data: { label: string; value: number; color?: string }[];
  onBarClick?: (item: { label: string; value: number }) => void;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="chart-3d-container flex items-end gap-2 h-[280px] p-4" dir="ltr">
      {data.map((d) => {
        const height = (d.value / max) * 200;
        const color = d.color || '#2fb36b';
        return (
          <button
            key={d.label}
            type="button"
            onClick={() => onBarClick?.(d)}
            className="chart-3d-bar flex-1 flex flex-col items-center justify-end gap-1 group"
            title={`${d.label}: ${d.value}`}
          >
            <div
              className="w-full rounded-t-lg transition-all duration-300 group-hover:brightness-125"
              style={{
                height: `${height}px`,
                background: `linear-gradient(to top, ${color}80, ${color})`,
                transform: 'translateZ(0)',
                boxShadow: `0 0 ${10 + (d.value / max) * 20}px ${color}40`,
              }}
              aria-hidden
            />
            <span className="text-[10px] text-[var(--color-night-200)]/50 whitespace-nowrap">{d.label}</span>
          </button>
        );
      })}
    </div>
  );
}
