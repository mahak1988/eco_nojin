import { useEffect, useRef, useState, useCallback } from 'react';
import { Satellite, Maximize } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import type { ImpactProject } from '../../content/pages/impactcarbon';
import type { Map as MapLibreMap, MapOptions, ControlPosition } from 'maplibre-gl';
import MapLayerPanel from './MapLayerPanel';

interface MapLibrePopup {
  setLngLat: (lngLat: [number, number]) => this;
  setHTML: (html: string) => this;
  addTo: (map: MapLibreMap) => this;
  remove: () => void;
}

type ProjectType = 'forest' | 'wetland' | 'agriculture';
type MapStyle = 'satellite' | 'ndvi' | 'ndwi' | 'true-color';
type DataLayer = 'soil' | 'water' | 'carbon';

const TYPE_COLORS: Record<ProjectType, string> = {
  forest: '#2fb36b',
  wetland: '#2a9bb5',
  agriculture: '#d49b3f',
};

const TYPE_LABELS_FA: Record<ProjectType, string> = {
  forest: 'جنگل‌کاری',
  wetland: 'بازگرداندن تالاب',
  agriculture: 'کشاورزی پایدار',
};

const TYPE_LABELS_EN: Record<ProjectType, string> = {
  forest: 'Forest restoration',
  wetland: 'Wetland restoration',
  agriculture: 'Sustainable agriculture',
};

const STYLE_LABELS_FA: Record<MapStyle, string> = {
  satellite: 'ماهواره‌ای',
  ndvi: 'NDVI (پوشش گیاهی)',
  ndwi: 'NDWI (آب)',
  'true-color': 'رنگ‌های واقعی',
};

const STYLE_LABELS_EN: Record<MapStyle, string> = {
  satellite: 'Satellite',
  ndvi: 'NDVI (Vegetation)',
  ndwi: 'NDWI (Water)',
  'true-color': 'True Color',
};

interface InteractiveSatelliteMapProps {
  projects: ImpactProject[];
  className?: string;
}

export default function InteractiveSatelliteMap({ projects, className }: InteractiveSatelliteMapProps) {
  const { t, lang } = useLang();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<MapStyle>('ndvi');
  const [activeDataLayers, setActiveDataLayers] = useState<DataLayer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const popupRef = useRef<MapLibrePopup | null>(null);
  const maplibreglRef = useRef<any>(null);

  // Dynamic import of maplibre-gl
  useEffect(() => {
    let mounted = true;
    let map: MapLibreMap | null = null;

    const initMap = async () => {
      try {
        const maplibreglModule = await import('maplibre-gl');
        const maplibreCssModule = await import('maplibre-gl/dist/maplibre-gl.css');
        const maplibreCss = (maplibreCssModule as any).default ?? maplibreCssModule;
        
        // Store module in ref for use in callbacks
        maplibreglRef.current = maplibreglModule;
        
        // Inject CSS
        if (document.head && !document.querySelector('link[href*="maplibre-gl.css"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = maplibreCss;
          document.head.appendChild(link);
        }

        if (!mounted || !mapContainerRef.current) return;

        // Initialize map
        const mapOptions: MapOptions = {
          container: mapContainerRef.current,
          style: getStyleUrl(selectedStyle),
          center: [54.0, 32.0], // Iran center
          zoom: 5,
          pitch: 0,
          bearing: 0,
          canvasContextAttributes: { antialias: true },
          attributionControl: false,
        };
        map = new maplibreglModule.Map(mapOptions);

        mapRef.current = map;

        map!.addControl(new maplibreglModule.NavigationControl({ showCompass: false }), 'top-right' as ControlPosition);
        map!.addControl(new maplibreglModule.ScaleControl({ unit: 'metric' }), 'bottom-right' as ControlPosition);
        map!.addControl(new maplibreglModule.AttributionControl({ compact: true }), 'bottom-left' as ControlPosition);

        map!.on('load', () => {
          if (mounted && map) {
            setIsLoading(false);
            addProjectMarkers(map);
          }
        });

        map!.on('error', (e: any) => {
          console.error('[MapLibre] Map error:', e);
          if (mounted) setError('خطا در بارگذاری نقشه');
        });

        map!.on('style.load', () => {
          if (mounted && map) addProjectMarkers(map);
        });

      } catch (err) {
        console.error('[MapLibre] Initialization failed:', err);
        if (mounted) {
          setError(err instanceof Error ? err.message : 'خطای ناشناخته');
          setIsLoading(false);
        }
      }
    };

    initMap();

    return () => {
      mounted = false;
      if (map) {
        map.remove();
      }
      if (popupRef.current) {
        popupRef.current.remove();
      }
    };
  }, []);

  const getStyleUrl = useCallback((style: MapStyle): string => {
    if (!import.meta.env.VITE_MAP_TILE_URL) {
      return 'https://demotiles.maplibre.org/style.json';
    }
    const baseUrl = import.meta.env.VITE_MAP_TILE_URL;
    const apiKey = import.meta.env.VITE_MAP_API_KEY || '';

    const styles: Record<MapStyle, string> = {
      satellite: `${baseUrl}/styles/satellite.json?key=${apiKey}`,
      ndvi: `${baseUrl}/styles/ndvi.json?key=${apiKey}`,
      ndwi: `${baseUrl}/styles/ndwi.json?key=${apiKey}`,
      'true-color': `${baseUrl}/styles/true-color.json?key=${apiKey}`,
    };

    return styles[style];
  }, [selectedStyle]);

  const addProjectMarkers = useCallback((map: MapLibreMap) => {
    if (!map.getSource('projects')) {
      map.addSource('projects', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: projects.map((project) => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [project.lng, project.lat],
            },
            properties: {
              name: project.name,
              type: project.type,
              status: project.status,
              ha: project.ha,
              co2e: project.co2e,
            },
          })),
        },
      });

      map.addLayer({
        id: 'projects-layer',
        type: 'circle',
        source: 'projects',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            4, 8,
            10, 16,
          ],
          'circle-color': [
            'match',
            ['get', 'type'],
            'forest', '#2fb36b',
            'wetland', '#2a9bb5',
            'agriculture', '#d49b3f',
            '#7ee2a8',
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.9,
        },
      });

      map.addLayer({
        id: 'projects-layer-hover',
        type: 'circle',
        source: 'projects',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            4, 12,
            10, 24,
          ],
          'circle-color': [
            'match',
            ['get', 'type'],
            'forest', '#7ee2a8',
            'wetland', '#7fd8e8',
            'agriculture', '#f2d49b',
            '#ffffff',
          ],
          'circle-opacity': 0,
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
        },
        filter: ['==', 'name', ''],
      });
    } else {
      const source = map.getSource('projects') as any;
      source.setData({
        type: 'FeatureCollection',
        features: projects.map((project) => ({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [project.lng, project.lat] },
          properties: {
            name: project.name,
            type: project.type,
            status: project.status,
            ha: project.ha,
            co2e: project.co2e,
          },
        })),
      });
    }

    // Hover effect
    map.on('mousemove', 'projects-layer', (e) => {
      if (e.features && e.features.length > 0) {
        map.getCanvas().style.cursor = 'pointer';
        const feature = e.features[0];
        const coords = feature.geometry.coordinates as [number, number];
        
        map.setFilter('projects-layer-hover', ['==', 'name', feature.properties.name]);
        
        showPopup(map, coords, feature.properties as ProjectProperties);
      }
    });

    map.on('mouseleave', 'projects-layer', () => {
      map.getCanvas().style.cursor = '';
      map.setFilter('projects-layer-hover', ['==', 'name', '']);
      if (popupRef.current) {
        popupRef.current.remove();
        popupRef.current = null;
      }
    });

    // Click to open Sentinel Hub
    map.on('click', 'projects-layer', (e) => {
      if (e.features && e.features.length > 0) {
        const feature = e.features[0];
        const coords = feature.geometry.coordinates as [number, number];
        window.open(
          `https://apps.sentinel-hub.eu/eo-browser/?zoom=12&lat=${coords[1]}&lng=${coords[0]}`,
          '_blank',
          'noopener,noreferrer'
        );
      }
    });
  }, [projects]);

  const showPopup = useCallback((map: MapLibreMap, coords: [number, number], properties: ProjectProperties) => {
    if (popupRef.current) {
      popupRef.current.remove();
    }

    const typeLabels = lang === 'fa' ? TYPE_LABELS_FA : TYPE_LABELS_EN;
    const statusLabels = lang === 'fa' 
      ? { planning: 'در برنامه', active: 'فعال', completed: 'تکمیل شده' }
      : { planning: 'Planning', active: 'Active', completed: 'Completed' };

    const PopupClass = maplibreglRef.current?.Popup;
    if (PopupClass) {
      popupRef.current = new PopupClass({ 
        closeButton: false,
        closeOnClick: false,
        anchor: 'bottom',
        offset: 15,
      })
        .setLngLat(coords)
        .setHTML(`
          <div class="p-3 min-w-[200px] text-[var(--color-night-950)]" style="font-family: 'Vazirmatn', sans-serif; direction: ${lang === 'fa' ? 'rtl' : 'ltr'};">
            <h4 class="font-extrabold text-sm mb-1">${properties.name}</h4>
            <p class="text-xs text-gray-600 mb-1">${typeLabels[properties.type]}</p>
            <p class="text-xs text-blue-600 mb-1">${statusLabels[properties.status as keyof typeof statusLabels]}</p>
            ${properties.ha ? `<p class="text-xs text-gray-500 mb-2">${properties.ha.toLocaleString(lang === 'fa' ? 'fa-IR' : 'en-US')} ha</p>` : ''}
            ${properties.co2e ? `<p class="text-xs text-green-600 mb-2">${properties.co2e.toLocaleString()} tCO₂e</p>` : ''}
            <a href="https://apps.sentinel-hub.eu/eo-browser/?zoom=12&lat=${coords[1]}&lng=${coords[0]}" 
               target="_blank" rel="noopener noreferrer"
               class="inline-flex items-center gap-1 text-xs font-bold text-green-600 hover:text-green-700">
              ${lang === 'fa' ? 'مشاهده در سنتینل هاب' : 'View on Sentinel Hub'}
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
            </a>
          </div>
        `)
        .addTo(map);
    }
  }, [lang]);

  const toggleDataLayer = useCallback((layer: DataLayer) => {
    setActiveDataLayers((prev) =>
      prev.includes(layer) ? prev.filter((l) => l !== layer) : [...prev, layer],
    );
  }, []);

  const handleStyleChange = useCallback((style: MapStyle) => {
    if (mapRef.current) {
      setSelectedStyle(style);
      mapRef.current.setStyle(getStyleUrl(style));
    }
  }, [getStyleUrl]);

  const toggleFullscreen = useCallback(() => {
    if (mapContainerRef.current) {
      if (!isFullscreen) {
        mapContainerRef.current.requestFullscreen?.();
      } else {
        document.exitFullscreen?.();
      }
      setIsFullscreen(!isFullscreen);
    }
  }, [isFullscreen]);

  // Handle fullscreen change
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
      if (mapRef.current) {
        setTimeout(() => mapRef.current?.resize(), 100);
      }
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Loading/Error states
  if (isLoading) {
    return (
      <section className={`px-4 py-12 sm:px-6 ${className || ''}`}>
        <Reveal className="mx-auto flex max-w-6xl flex-col gap-8">
          <div className="flex flex-col items-center text-center">
            <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
              {t.impact.mapTitle}
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">
              {t.impact.mapNote}
            </p>
          </div>
        </Reveal>
        <Reveal delay={0.2}>
          <div className="relative mx-auto h-[480px] w-full max-w-5xl overflow-hidden rounded-3xl border border-[var(--color-leaf-500)]/20">
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--color-night-900)]">
              <div className="flex flex-col items-center gap-4">
                <div className="h-10 w-10 animate-spin rounded-full border-3 border-[var(--color-leaf-500)]/25 border-t-leaf-400" />
                <span className="text-sm text-[var(--color-night-200)]/50">
                  {lang === 'fa' ? 'در حال بارگذاری نقشه...' : 'Loading map...'}
                </span>
              </div>
            </div>
          </div>
        </Reveal>
      </section>
    );
  }

  if (error) {
    return (
      <section className={`px-4 py-12 sm:px-6 ${className || ''}`}>
        <Reveal className="mx-auto flex max-w-6xl flex-col gap-8">
          <div className="flex flex-col items-center text-center">
            <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
              {t.impact.mapTitle}
            </h2>
          </div>
        </Reveal>
        <Reveal delay={0.2}>
          <div className="relative mx-auto h-[480px] w-full max-w-5xl overflow-hidden rounded-3xl border border-red-500/20">
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--color-night-900)] p-8">
              <div className="text-center">
                <div className="text-4xl mb-4">🗺️</div>
                <h3 className="text-lg font-bold text-red-300 mb-2">
                  {lang === 'fa' ? 'خطا در بارگذاری نقشه' : 'Failed to load map'}
                </h3>
                <p className="text-sm text-[var(--color-night-200)]/60 mb-4">{error}</p>
                <p className="text-xs text-[var(--color-night-200)]/40">
                  {lang === 'fa' 
                    ? 'برای مشاهده نقشه تعاملی، سرویس تایل‌های ماهواره‌ای باید پیکربندی شود.' 
                    : 'Map tile service must be configured for interactive map.'}
                </p>
              </div>
            </div>
          </div>
        </Reveal>
      </section>
    );
  }

  return (
    <section className={`px-4 py-12 sm:px-6 ${className || ''}`}>
      <Reveal className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex flex-col items-center text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
            {t.impact.mapTitle}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">
            {t.impact.mapNote}
          </p>
        </div>
      </Reveal>

      <Reveal delay={0.2}>
        <div className="relative mx-auto max-w-5xl">
          <div 
            ref={mapContainerRef}
            className={`h-[480px] w-full rounded-3xl border border-[var(--color-leaf-500)]/20 overflow-hidden ${isFullscreen ? 'fixed inset-0 z-50 rounded-none border-none' : ''}`}
            style={{ touchAction: 'pan-x pan-y' }}
          />

          {/* Map Controls */}
          <div className="absolute top-4 start-4 z-10 flex items-center gap-2 flex-wrap">
            <div className="glass glass-hover flex items-center gap-1 rounded-xl bg-[var(--color-night-900)] px-3 py-1.5" role="group" aria-label={lang === 'fa' ? 'انتخاب لایه نقشه' : 'Map layer selection'}>
              {(['satellite', 'ndvi', 'ndwi', 'true-color'] as MapStyle[]).map((style) => (
                <button
                  key={style}
                  type="button"
                  onClick={() => handleStyleChange(style)}
                  className={`rounded-lg px-3 py-1.5 text-[11px] font-bold transition-all ${selectedStyle === style ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]' : 'text-[var(--color-night-200)]/60 hover:bg-white/5 hover:text-[var(--color-night-100)]'}`}
                  aria-pressed={selectedStyle === style}
                >
                  {lang === 'fa' ? STYLE_LABELS_FA[style] : STYLE_LABELS_EN[style]}
                </button>
              ))}
            </div>

            <MapLayerPanel
              activeLayers={activeDataLayers}
              onToggle={toggleDataLayer}
            />

            <button
              type="button"
              onClick={toggleFullscreen}
              className="glass glass-hover inline-flex items-center gap-1.5 rounded-xl bg-[var(--color-night-900)] px-3 py-1.5 text-[11px] font-bold text-[var(--color-night-100)]"
              aria-label={isFullscreen ? (lang === 'fa' ? 'خروج از تمام‌صفحه' : 'Exit fullscreen') : (lang === 'fa' ? 'تمام‌صفحه' : 'Fullscreen')}
            >
              <Maximize className="h-4 w-4" aria-hidden />
            </button>
          </div>

          {/* Satellite indicator */}
          <div className="absolute top-4 end-4 z-10">
            <div className="glass inline-flex items-center gap-2 rounded-full bg-[var(--color-night-900)] px-3 py-1.5">
              <Satellite className="h-4 w-4 text-[var(--color-aqua-500)]" />
              <span className="text-[10px] font-bold text-[var(--color-night-200)]/60">
                {lang === 'fa' ? 'سنتینل-۲ (کوپرنیکوس)' : 'Sentinel-2 (Copernicus)'}
              </span>
            </div>
          </div>

          {/* Legend */}
          <div className="absolute bottom-3 start-3 z-10 glass rounded-xl bg-[var(--color-night-950)]/80 px-3 py-2 backdrop-blur-sm">
            {Object.entries(TYPE_LABELS_FA).map(([key]) => {
              const typeKey = key as ProjectType;
              return (
                <div key={key} className="flex items-center gap-1.5">
                  <div className="h-3 w-3 rounded-full" style={{ background: TYPE_COLORS[typeKey] }} aria-hidden />
                  <span className="text-[10px] font-bold text-[var(--color-night-200)]/60">
                    {lang === 'fa' ? TYPE_LABELS_FA[typeKey] : TYPE_LABELS_EN[typeKey]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </Reveal>

      <Reveal delay={0.4}>
        <p className="mx-auto max-w-3xl text-center text-[10px] text-[var(--color-night-200)]/35">
          {lang === 'fa'
            ? 'نقشه تعاملی شامل لایه‌های NDVI، NDWI، رنگ‌های واقعی و ماهواره‌ای؛ مارکرهای پروژه با لینک مستقیم به Sentinel Hub EO Browser.'
            : 'Interactive map with NDVI, NDWI, True Color, and Satellite layers; project markers link directly to Sentinel Hub EO Browser.'}
        </p>
      </Reveal>
    </section>
  );
}

interface ProjectProperties {
  name: string;
  type: ProjectType;
  status: 'planning' | 'active' | 'completed';
  ha?: number;
  co2e?: number;
}
