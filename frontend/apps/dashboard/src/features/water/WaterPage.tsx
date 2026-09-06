import { useState } from 'react';
import { useWaterBalance } from '@eco/api/hooks/use-water';
import { LineChart } from '@eco/charts';
import { GeoJsonLayer, MapMarker, MapView } from '@eco/geo';
import { Card, CardBody, CardHeader, Spinner } from '@eco/ui';
import type { FeatureCollection } from 'geojson';

const DEMO_BBOX = { south: 35.6, west: 51.3, north: 35.75, east: 51.55 } as const;
const DEMO_RIVER: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { kind: 'river', name: 'Demo River' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [51.32, 35.72],
          [51.36, 35.7],
          [51.4, 35.68],
          [51.44, 35.66],
          [51.48, 35.64],
        ],
      },
    },
  ],
};

export function WaterPage() {
  const [start, setStart] = useState('2025-01-01');
  const [end, setEnd] = useState('2025-12-31');

  const balance = useWaterBalance({
    bounds: { ...DEMO_BBOX },
    start,
    end,
    timestep: 'monthly',
  });

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">Water balance</h1>
        <p className="text-sm text-ink-muted">
          Daily / monthly precipitation, ET₀, runoff, and groundwater recharge.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Range</h2>
        </CardHeader>
        <CardBody className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            Start
            <input
              type="date"
              value={start}
              onChange={(e) => setStart((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            End
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </label>
        </CardBody>
      </Card>

      {balance.isLoading && (
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Spinner size="sm" /> Loading water balance…
        </div>
      )}

      {balance.data && (
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Hydrological fluxes</h2>
          </CardHeader>
          <CardBody>
            <LineChart
              height={360}
              series={[
                { name: 'Precip', data: balance.data.timestamps.map((t, i) => ({ x: t, y: balance.data!.precipitation_mm[i] ?? 0 })) },
                { name: 'ET₀', data: balance.data.timestamps.map((t, i) => ({ x: t, y: balance.data!.et0_mm[i] ?? 0 })) },
                { name: 'Runoff', data: balance.data.timestamps.map((t, i) => ({ x: t, y: balance.data!.runoff_mm[i] ?? 0 })) },
                { name: 'Recharge', data: balance.data.timestamps.map((t, i) => ({ x: t, y: balance.data!.recharge_mm[i] ?? 0 })) },
              ]}
              yLabel="mm"
            />
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Watershed map</h2>
        </CardHeader>
        <CardBody>
          <MapView
            initialLatitude={0.5 * (DEMO_BBOX.south + DEMO_BBOX.north)}
            initialLongitude={0.5 * (DEMO_BBOX.west + DEMO_BBOX.east)}
            initialZoom={9}
            height={420}
          >
            <GeoJsonLayer id="river" data={DEMO_RIVER} type="line" color="#0ea5e9" />
            <MapMarker
              latitude={35.68}
              longitude={51.4}
              color="#0ea5e9"
              label="Outlet"
              popup={<span className="text-xs">Watershed outlet (demo)</span>}
            />
          </MapView>
          <p className="mt-3 text-xs text-ink-muted">
            Showing the demo watershed bounding box. Real HEC-RAS / SWAT outputs will replace the demo layer once the backend exposes them.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}