import { useEffect, useState } from 'react';

/** Satellite imagery feed preview with scan animation. */
export default function SatelliteFeedPreview({
  projectName = 'جنگلشکاری مشهد',
}: {
  projectName?: string;
}) {
  const [scanning, setScanning] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => setScanning((s) => !s), 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="rounded-3xl glass overflow-hidden relative">
      <div className="h-[200px] bg-gradient-to-br from-[var(--color-night-800)] to-[var(--color-night-700)] relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              'linear-gradient(rgba(47,179,107,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(47,179,107,0.1) 1px, transparent 1px)',
            backgroundSize: '30px 30px',
          }}
          aria-hidden
        />
        <div
          className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[var(--color-leaf-500)] to-transparent transition-all duration-1000"
          style={{
            top: scanning ? '40%' : '60%',
            opacity: scanning ? 1 : 0.5,
          }}
          aria-hidden
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <span className="live-dot inline-block mb-2" aria-hidden />
            <p className="text-xs text-[var(--color-leaf-300)] font-bold">{scanning ? 'پخش زنده ماهواره‌ای' : 'اتصال مجدد...'}</p>
            <p className="text-[10px] text-[var(--color-night-200)]/40 mt-1">{projectName}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
