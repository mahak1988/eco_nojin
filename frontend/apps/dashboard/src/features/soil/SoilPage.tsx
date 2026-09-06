import { useState } from 'react';
import { useSoilProfile } from '@eco/api/hooks/use-soil';
import type { GeoBounds } from '@eco/api/schema/common';
import { GeoBoundsSchema } from '@eco/api/schema/common';
import { Card, CardBody, CardHeader, EmptyState, Input, Spinner } from '@eco/ui';

const DEFAULT_BOUNDS: GeoBounds = GeoBoundsSchema.parse({
  south: 35.6,
  west: 51.3,
  north: 35.75,
  east: 51.55,
});

export function SoilPage() {
  const [bounds, setBounds] = useState<GeoBounds>(DEFAULT_BOUNDS);
  const [text, setText] = useState(() => JSON.stringify(DEFAULT_BOUNDS));

  const profile = useSoilProfile(bounds);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">Soil profiles</h1>
        <p className="text-sm text-ink-muted">
          SoilGrids-backed soil organic carbon, texture, and bulk density by bounds.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Query bounds</h2>
        </CardHeader>
        <CardBody className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            GeoJSON bounds (south, west, north, east)
            <Input
              value={text}
              onChange={(e) => setText((e.target as HTMLInputElement).value)}
              onBlur={() => {
                try {
                  setBounds(GeoBoundsSchema.parse(JSON.parse(text)));
                } catch {
                  /* keep previous on parse failure */
                }
              }}
              className="font-mono"
            />
          </label>
        </CardBody>
      </Card>

      {profile.isLoading && (
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Spinner size="sm" /> Loading soil profile…
        </div>
      )}

      {profile.data && (
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Layers</h2>
          </CardHeader>
          <CardBody>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-start text-xs uppercase text-ink-muted">
                  <th className="py-2 text-start">Depth</th>
                  <th className="py-2 text-start">Texture</th>
                  <th className="py-2 text-start">OC %</th>
                  <th className="py-2 text-start">Bulk density</th>
                  <th className="py-2 text-start">pH</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink/5">
                {profile.data.layers.map((l) => (
                  <tr key={l.depth_cm}>
                    <td className="py-2">{l.depth_cm} cm</td>
                    <td className="py-2">{l.texture}</td>
                    <td className="py-2">{l.organic_carbon_pct.toFixed(2)}</td>
                    <td className="py-2">{l.bulk_density_g_cm3.toFixed(2)} g/cm³</td>
                    <td className="py-2">{l.ph.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardBody>
        </Card>
      )}

      {profile.error && (
        <EmptyState
          title="Soil profile error"
          description={(profile.error as Error).message}
        />
      )}
    </div>
  );
}