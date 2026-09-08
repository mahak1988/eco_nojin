/**
 * Fixed page backdrop: gradient orbs, faint grid and vignette.
 * Purely decorative — sits behind all content.
 */
export default function Backdrop() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden>
      {/* base gradient */}
      <div className="absolute inset-0 bg-night-950" />
      {/* grid */}
      <div className="absolute inset-0 bg-grid" />
      {/* emerald orb */}
      <div
        className="absolute -top-32 start-[-10%] h-[480px] w-[480px] rounded-full opacity-25 blur-[130px]"
        style={{ background: 'radial-gradient(circle, #2fb36b 0%, transparent 70%)' }}
      />
      {/* aqua orb */}
      <div
        className="absolute top-[30%] end-[-12%] h-[520px] w-[520px] rounded-full opacity-20 blur-[140px]"
        style={{ background: 'radial-gradient(circle, #2a9bb5 0%, transparent 70%)' }}
      />
      {/* sand orb */}
      <div
        className="absolute bottom-[-14%] start-[28%] h-[420px] w-[420px] rounded-full opacity-10 blur-[130px]"
        style={{ background: 'radial-gradient(circle, #d49b3f 0%, transparent 70%)' }}
      />
      {/* vignette */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 120% 90% at 50% 40%, transparent 55%, rgba(2,8,6,0.75) 100%)',
        }}
      />
    </div>
  );
}
