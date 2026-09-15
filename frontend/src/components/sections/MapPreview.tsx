import { useEffect, useRef, useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { MapPin, Satellite } from 'lucide-react';
import Reveal from '../ui/Reveal';
import type { Map as MapLibreMap } from 'maplibre-gl';

interface ProjectMarker {
  name: string;
  lat: number;
  lng: number;
  type: 'forest' | 'wetland' | 'agriculture';
  status: 'planning' | 'active' | 'completed';
}

const TYPE_COLORS = { forest: '#2fb36b', wetland: '#2a9bb5', agriculture: '#d49b3f' };
const TYPE_LABELS = { forest: 'جنگل', wetland: 'تالاب', agriculture: 'کشاورزی' };

const SAMPLE_MARKERS: ProjectMarker[] = [
  { name: 'مشهد', lat: 36.3, lng: 59.6, type: 'forest', status: 'active' },
  { name: 'اهواز', lat: 31.3, lng: 48.5, type: 'wetland', status: 'planning' },
  { name: 'اصفهان', lat: 32.4, lng: 51.7, type: 'agriculture', status: 'completed' },
  { name: 'رشت', lat: 37.3, lng: 49.6, type: 'wetland', status: 'active' },
  { name: 'تبریز', lat: 38.0, lng: 46.3, type: 'forest', status: 'planning' },
];

/** Mini interactive map preview on HomePage. */
export default function MapPreview() {
  const { lang } = useLang();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;

    const initMap = async () => {
      try {
        const maplibreglModule = await import('maplibre-gl');
        const maplibreCssModule = await import('maplibre-gl/dist/maplibre-gl.css');
        const maplibreCss = String((maplibreCssModule as { default: string }).default);

        if (document.head && !document.querySelector('link[href*="maplibre-gl.css"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = maplibreCss;
          document.head.appendChild(link);
        }

        if (!mounted || !mapContainerRef.current) return;

        const map = new maplibreglModule.Map({
          container: mapContainerRef.current,
          style: 'https://demotiles.maplibre.org/style.json',
          center: [54.0, 32.0],
          zoom: 4,
          attributionControl: false,
        });

        mapRef.current = map;

        map.on('load', () => {
          if (!mounted) return;
          setLoaded(true);

          map.addSource('projects', {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: SAMPLE_MARKERS.map((m) => ({
                type: 'Feature',
                geometry: { type: 'Point', coordinates: [m.lng, m.lat] },
                properties: { name: m.name, type: m.type, status: m.status },
              })),
            },
          });

          map.addLayer({
            id: 'projects-layer',
            type: 'circle',
            source: 'projects',
            paint: {
              'circle-radius': 8,
              'circle-color': ['match', ['get', 'type'], 'forest', '#2fb36b', 'wetland', '#2a9bb5', 'agriculture', '#d49b3f', '#7ee2a8'],
              'circle-stroke-width': 2,
              'circle-stroke-color': '#ffffff',
              'circle-opacity': 0.9,
            },
          });

          map.on('click', 'projects-layer', (e) => {
            const feature = e.features?.[0];
            if (feature) {
              const name = (feature.properties as { name?: string }).name;
              map!.flyTo({ center: [54.0, 32.0] as [number, number], zoom: 6 });
              new maplibreglModule.Popup({ closeButton: false, offset: 15 })
                .setLngLat([54.0, 32.0] as [number, number])
                .setHTML(`<div class="p-2 text-sm font-bold" style="font-family:'Vazirmatn',sans-serif">${name}</div>`)
                .addTo(map!);
            }
          });
        });
      } catch {
        setLoaded(true);
      }
    };

    initMap();

    return () => {
      mounted = false;
      if (mapRef.current) mapRef.current.remove();
    };
  }, []);

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="map-preview" aria-labelledby="map-heading">
        <div className="mx-auto max-w-6xl">
          <div className="mb-6 flex items-center gap-2">
            <Satellite className="h-5 w-5 text-[var(--color-aqua-500)]" aria-hidden />
            <p className="text-sm font-extrabold text-[var(--color-aqua-300)]">پایش ماهواره‌ای</p>
          </div>
          <h2 id="map-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
            {lang === 'fa' ? 'پروژه‌های زنده ماهواره‌ای' : 'Live Satellite Projects'}
          </h2>

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
            <div
              ref={mapContainerRef}
              className={`h-[400px] w-full overflow-hidden rounded-3xl border border-[var(--color-leaf-500)]/20 ${!loaded ? 'bg-[var(--color-night-900)] flex items-center justify-center' : ''}`}
              style={{ touchAction: 'pan-x pan-y' }}
            >
              {!loaded && (
                <div className="flex flex-col items-center gap-3">
                  <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-leaf-500)]/25 border-t-leaf-400" />
                  <span className="text-sm text-[var(--color-night-200)]/50">{lang === 'fa' ? 'در حال بارگذاری نقشه...' : 'Loading map...'}</span>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3">
              {SAMPLE_MARKERS.map((marker) => (
                <div key={marker.name} className="glass rounded-2xl p-4 flex items-center gap-3">
                  <div className="h-3 w-3 rounded-full" style={{ background: TYPE_COLORS[marker.type] }} aria-hidden />
                  <div>
                    <p className="text-sm font-bold text-[var(--color-night-100)]">{marker.name}</p>
                    <p className="text-xs text-[var(--color-night-200)]/50">
                      {TYPE_LABELS[marker.type]} · {marker.status === 'active' ? 'فعال' : marker.status === 'planning' ? 'در برنامه' : 'تکمیل شده'}
                    </p>
                  </div>
                  <MapPin className="ml-auto h-4 w-4 text-[var(--color-night-200)]/40" aria-hidden />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </Reveal>
  );
}
