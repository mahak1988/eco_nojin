/** Animated metric counter widget. */
export default function CounterWidget({
  value,
  label,
  suffix = '',
  prefix = '',
}: {
  value: number;
  label: string;
  suffix?: string;
  prefix?: string;
}) {
  return (
    <div className="rounded-2xl glass p-4 embossed">
      <p className="text-3xl font-extrabold text-[var(--color-leaf-300)]">
        {prefix}{value.toLocaleString()}{suffix}
      </p>
      <p className="text-xs text-[var(--color-night-200)]/60 mt-1">{label}</p>
    </div>
  );
}
