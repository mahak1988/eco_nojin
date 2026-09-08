/** Marquee strip of HyDroMa model names — an editorial, continuous ribbon. */

const MODELS = [
  'Richards',
  'Saint-Venant',
  'FAO-56',
  'RUSLE',
  'SWAT',
  'RothC',
  'AquaCrop',
  'NSGA-II',
  'HEC-RAS',
  'Sentinel-2',
  'ERA5',
  'SoilGrids',
];

/** Continuous model-name ribbon (duplicated for a seamless loop). */
export default function ModelsMarquee() {
  const items = [...MODELS, ...MODELS];

  return (
    <div className="relative overflow-hidden border-y border-white/8 bg-white/2 py-5" aria-hidden>
      <div
        className="pointer-events-none absolute inset-y-0 start-0 z-10 w-24"
        style={{ background: 'linear-gradient(to right, #04100b, transparent)' }}
      />
      <div
        className="pointer-events-none absolute inset-y-0 end-0 z-10 w-24"
        style={{ background: 'linear-gradient(to left, #04100b, transparent)' }}
      />
      <div className="flex w-max items-center gap-10 px-5 animate-marquee">
        {items.map((model, index) => (
          <span key={model + index} className="flex items-center gap-10">
            <span dir="ltr" className="text-lg font-extrabold tracking-wide text-emerald-100/45">
              {model}
            </span>
            <span className="h-1.5 w-1.5 rounded-full bg-leaf-500/60" />
          </span>
        ))}
      </div>
    </div>
  );
}
