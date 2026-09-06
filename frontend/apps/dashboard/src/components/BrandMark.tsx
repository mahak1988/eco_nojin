/**
 * Brand mark for Eco Nojin — shared between web and dashboard.
 */
export function BrandMark({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Eco Nojin"
    >
      <defs>
        <linearGradient id="brand-gradient" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#af5f1e" />
          <stop offset="50%" stopColor="#dca164" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#brand-gradient)" />
      <path
        d="M5 22 Q11 14 16 14 Q21 14 27 22"
        stroke="white"
        strokeWidth="1.8"
        strokeLinecap="round"
        fill="none"
        opacity={0.9}
      />
      <circle cx="22" cy="11" r="2.5" fill="white" opacity={0.95} />
      <path d="M16 14 Q13 10 13 7" stroke="white" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <path d="M16 14 Q19 11 20 9" stroke="white" strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <path d="M16 14 L16 21" stroke="white" strokeWidth="1.8" strokeLinecap="round" fill="none" />
    </svg>
  );
}

export function BrandWordmark({
  size = 'md',
  className,
  variant = 'light',
}: {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  variant?: 'light' | 'dark';
}) {
  const markSize = size === 'lg' ? 40 : size === 'sm' ? 24 : 32;
  const mainColor = variant === 'light' ? 'text-ink' : 'text-ink-inverse';
  const subColor = variant === 'light' ? 'text-ink-muted' : 'text-ink-inverse/60';
  return (
    <div className={`inline-flex items-center gap-2 ${className ?? ''}`}>
      <BrandMark size={markSize} />
      <div className="flex flex-col leading-none">
        <span className={`${size === 'lg' ? 'text-xl' : size === 'sm' ? 'text-sm' : 'text-base'} font-semibold tracking-tight ${mainColor}`}>
          Eco Nojin
        </span>
        <span className={`text-[10px] font-medium uppercase tracking-[0.18em] ${subColor}`}>
          اکو نُژین
        </span>
      </div>
    </div>
  );
}