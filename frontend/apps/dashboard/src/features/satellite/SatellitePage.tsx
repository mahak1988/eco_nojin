import { useState } from 'react';
import { useSatelliteIndexSeries } from '@eco/api/hooks/use-satellite';
import type { SatelliteSource } from '@eco/api/schema/satellite';
import { LineChart } from '@eco/charts';
import { GeoJsonLayer, MapMarker, MapView, bboxToMaplibreBounds, expandBounds } from '@eco/geo';
import { Card, CardBody, CardHeader, EmptyState, Skeleton, Spinner } from '@eco/ui';
import type { FeatureCollection } from 'geojson';

const DEMO_BOUNDS = { south: 35.6, west: 51.3, north: 35.75, east: 51.55 } as const;

const DEMO_FARM: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Demo Farm', area_ha: 42 },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [51.38, 35.68],
            [51.39, 35.68],
            [51.39, 35.69],
            [51.38, 35.69],
            [51.38, 35.68],
          ],
        ],
      },
    },
  ],
};

export function SatellitePage() {
  const [source, setSource] = useState<SatelliteSource>('sentinel2');
  const [index, setIndex] = useState<'NDVI' | 'NDWI' | 'EVI' | 'LAI' | 'SAVI'>('NDVI');

  const series = useSatelliteIndexSeries({
    source,
    index,
    bounds: { ...DEMO_BOUNDS },
    start: '2025-01-01',
    end: '2025-12-31',
  });

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">🛰️ Satellite indices</h1>
        <p className="text-sm text-ink-muted">
          Time series of vegetation / water indices from Sentinel, Landsat, MODIS, ERA5.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Source &amp; index</h2>
        </CardHeader>
        <CardBody className="flex flex-wrap gap-3">
          <select
            value={source}
            onChange={(e) => setSource((e.target as HTMLSelectElement).value as SatelliteSource)}
            className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
          >
            <option value="sentinel2">Sentinel-2</option>
            <option value="sentinel1">Sentinel-1</option>
            <option value="landsat8">Landsat 8</option>
            <option value="modis">MODIS</option>
            <option value="era5">ERA5</option>
          </select>
          <select
            value={index}
            onChange={(e) => setIndex((e.target as HTMLSelectElement).value as typeof index)}
            className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
          >
            <option value="NDVI">NDVI</option>
            <option value="NDWI">NDWI</option>
            <option value="EVI">EVI</option>
            <option value="LAI">LAI</option>
            <option value="SAVI">SAVI</option>
          </select>
        </CardBody>
      </Card>

      {series.isLoading && (
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Spinner size="sm" /> Fetching satellite composites…
        </div>
      )}

      {series.data && (
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">
              {index} time series — {source}
            </h2>
          </CardHeader>
          <CardBody>
            <LineChart
              height={360}
              series={[
                {
                  name: index,
                  data: series.data.values.map((v) => ({ x: v.date, y: v.value })),
                  area: true,
                },
              ]}
              yLabel={index}
            />
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Spatial context</h2>
        </CardHeader>
        <CardBody>
          <MapView
            initialLatitude={0.5 * (DEMO_BOUNDS.south + DEMO_BOUNDS.north)}
            initialLongitude={0.5 * (DEMO_BOUNDS.west + DEMO_BOUNDS.east)}
            initialZoom={11}
            height={420}
          >
            <GeoJsonLayer id="farm-boundary" data={DEMO_FARM} type="fill" color="#16a34a" />
            <MapMarker
              latitude={0.5 * (DEMO_BOUNDS.south + DEMO_BOUNDS.north)}
              longitude={0.5 * (DEMO_BOUNDS.west + DEMO_BOUNDS.east)}
              color="#16a34a"
              label="Demo farm centroid"
              popup={
                <div className="text-xs">
                  <strong>Demo farm</strong>
                  <div>BBox: {JSON.stringify(expandBounds(DEMO_BOUNDS, 0.5))}</div>
                </div>
              }
            />
          </MapView>
          <p className="mt-3 text-xs text-ink-muted">
            Map uses MapLibre + OpenFreeMap tiles (no API key). Draw area-of-interest with the navigation control.
          </p>
          <p className="mt-1 text-xs text-ink-subtle">
            Bounds: {JSON.stringify(bboxToMaplibreBounds(DEMO_BOUNDS))}
          </p>
        </CardBody>
      </Card>

      {!series.data && !series.isLoading && (
        <EmptyState
          title="No satellite data yet"
          description="Backend may not be reachable, or the selected bounds have no scenes."
        />
      )}
    </div>
  );
}

// keep Skeleton referenced in case it is needed later
export const _SkeletonPlaceholder = Skeleton;