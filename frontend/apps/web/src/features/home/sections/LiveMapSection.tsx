import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Reveal } from '@eco/ui';

/**
 * Live map section — real geospatial context with MapLibre.
 * Loads the map lazily (code-split) and degrades gracefully when the demo
 * tile service is unreachable.
 */
export function LiveMapSection() {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let map: { remove: () => void } | null = null;
    let cancelled = false;

    (async () => {
      try {
        const maplibregl = (await import('maplibre-gl')).default;
        await import('maplibre-gl/dist/maplibre-gl.css');
        if (cancelled || !containerRef.current) return;
        map = new maplibregl.Map({
          container: containerRef.current,
          style: 'https://demotiles.maplibre.org/style.json',
          center: [54, 32],
          zoom: 3.2,
          attributionControl: false,
        });
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
      try {
        map?.remove();
      } catch {
        /* noop */
      }
    };
  }, []);

  return (
    <section className="bg-surface py-24 lg:py-32">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-medium text-ink-subtle">{t('home.map.badge', 'دادهٔ جغرافیایی زنده')}</p>
            <h2 className="mt-3 text-balance text-4xl font-bold tracking-tight sm:text-5xl">
              {t('home.map.title', 'از ماهواره تا نقشهٔ تصمیم')}
            </h2>
            <p className="mt-4 text-balance text-base text-ink-muted md:text-lg">
              {t('home.map.subtitle', 'لایه‌های NDVI، خاک و آب در یک نگاه — همان موتوری که در HyDroMa اجرا می‌شود.')}
            </p>
          </div>
        </Reveal>

        <Reveal delay={120} className="mt-14">
          <div className="overflow-hidden rounded-[28px] border border-ink/10 shadow-soft">
            <div className="relative h-[440px] w-full bg-surface-muted dark:bg-slate-900">
              {failed ? (
                <div className="flex h-full w-full flex-col items-center justify-center gap-3 p-8 text-center">
                  <span className="text-3xl" aria-hidden="true">🛰️</span>
                  <p className="text-sm font-medium text-ink">{t('home.map.fallbackTitle', 'نقشهٔ تعاملی موقتاً در دسترس نیست')}</p>
                  <p className="max-w-md text-xs leading-relaxed text-ink-muted">
                    {t('home.map.fallbackBody', 'سرویس کاشی نقشه در این شبکه پاسخ نداد؛ در HyDroMa لایه‌های کامل ماهواره‌ای و GIS در دسترس شماست.')}
                  </p>
                </div>
              ) : (
                <div ref={containerRef} className="h-full w-full" aria-label={t('home.map.aria', 'نقشهٔ تعاملی جهان')} />
              )}

              {/* Legend overlay */}
              <div className="glass pointer-events-none absolute bottom-4 start-4 z-10 rounded-2xl px-4 py-3 text-xs shadow-soft">
                <div className="flex items-center gap-2 font-semibold text-ink">
                  <span className="inline-block h-2 w-2 rounded-full bg-leaf-500" aria-hidden="true" />
                  {t('home.map.legend', 'نمای کلی حوضه‌ها و پوشش زمین')}
                </div>
                <div className="mt-1 text-ink-muted">{t('home.map.legendHint', 'برای کاوش، نقشه را جابه‌جا و بزرگ‌نمایی کنید')}</div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
