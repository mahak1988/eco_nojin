interface LogoProps {
  size?: number;
  withWordmark?: boolean;
  wordmark?: string;
}

/**
 * Brand mark: a leaf inside an orbital ellipse with a satellite dot —
 * the meeting point of agriculture and remote sensing.
 */
export default function Logo({ size = 40, withWordmark = true, wordmark }: LogoProps) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        role="img"
        aria-label="Eco Nojin"
        className="shrink-0"
      >
        <defs>
          <linearGradient id="logo-leaf" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#7ee2a8" />
            <stop offset="1" stopColor="#2a9bb5" />
          </linearGradient>
        </defs>
        <rect width="64" height="64" rx="14" fill="rgba(255,255,255,0.05)" />
        <ellipse
          cx="32"
          cy="32"
          rx="24"
          ry="10.5"
          fill="none"
          stroke="#2fb36b"
          strokeOpacity="0.6"
          strokeWidth="1.6"
          transform="rotate(-24 32 32)"
        />
        <circle cx="52.5" cy="21.5" r="2.6" fill="#e6b96b" />
        <path d="M32 44c0-11 7.5-17.5 15-19.5C47 36 40.5 44 32 44Z" fill="url(#logo-leaf)" />
        <path d="M32 44c0-9-5.5-14.5-11-16C21 37 25.5 43 32 44Z" fill="#2fb36b" fillOpacity="0.8" />
        <path
          d="M32 44V30"
          stroke="#04100b"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
      {withWordmark ? (
        <span className="flex flex-col leading-tight">
          <span className="text-lg font-extrabold text-emerald-50">{wordmark}</span>
          <span className="text-[10px] font-medium tracking-[0.2em] text-leaf-300/80">
            ECO NOJIN
          </span>
        </span>
      ) : null}
    </span>
  );
}
