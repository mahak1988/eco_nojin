/** Page backdrop v3 — Design-Horizons ambience: layered eco glows, a faint
 * dot grid, and a vignette that keeps edges dark and content focused. */

export default function Backdrop() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden>
      <div className="absolute inset-0 bg-night-950" />
      {/* layered ambient glows (leaf top-left, aqua top-right, gold floor) */}
      <div className="ambient-glow absolute inset-0" />
      {/* faint dot grid, fading out toward the bottom */}
      <div
        className="bg-dot-grid absolute inset-x-0 top-0 h-[70vh]"
        style={{
          maskImage: 'linear-gradient(to bottom, rgba(0,0,0,0.8), transparent 85%)',
          WebkitMaskImage: 'linear-gradient(to bottom, rgba(0,0,0,0.8), transparent 85%)',
        }}
      />
      {/* vignette keeps edges dark and content focused */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 120% 90% at 50% 35%, transparent 55%, rgba(3,10,7,0.82) 100%)',
        }}
      />
    </div>
  );
}
