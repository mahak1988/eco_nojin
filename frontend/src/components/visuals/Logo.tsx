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
      <img
        src="/logo-econojin.png"
        alt="Eco Nojin"
        width={size}
        height={size}
        className="shrink-0 rounded-xl object-cover"
      />
      {withWordmark ? (
        <span className="flex flex-col leading-tight">
          <span className="text-lg font-extrabold text-[var(--color-night-100)]">{wordmark}</span>
          <span className="text-[10px] font-medium tracking-[0.2em] text-[var(--color-leaf-300)]/80">
            ECO NOJIN
          </span>
        </span>
      ) : null}
    </span>
  );
}
