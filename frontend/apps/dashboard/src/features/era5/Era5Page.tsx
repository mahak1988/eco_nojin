import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { LineChart } from '@eco/charts';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard } from '@eco/ui';

type Era5Response = {
  series?: Array<{ date: string; t2m?: number; tp?: number }>;
  unit?: string;
  summary?: { min: number; max: number; mean: number };
};

export function Era5Page() {
  const { t } = useTranslation();
  const [lat, setLat] = useState('35.6892');
  const [lon, setLon] = useState('51.389');
  const [start, setStart] = useState('2025-01-01');
  const [end, setEnd] = useState('2025-12-31');

  const run = useRunMotorEndpoint<Era5Response>('/api/v1/satellite/era5/series');

  function submit() {
    run.mutate({
      latitude: Number(lat),
      longitude: Number(lon),
      start,
      end,
    });
  }

  const seriesData = run.data?.series ?? [];
  const tempSeries = seriesData
    .filter((s): s is { date: string; t2m: number } => typeof s.t2m === 'number')
    .map((s) => ({ x: s.date, y: s.t2m }));
  const precipSeries = seriesData
    .filter((s): s is { date: string; tp: number } => typeof s.tp === 'number')
    .map((s) => ({ x: s.date, y: s.tp }));

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.era5.title', '🌤️ ERA5 reanalysis')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.era5.subtitle', 'Hourly 0.25° ERA5 reanalysis for temperature and precipitation.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.era5.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label={t('dashboard.pages.era5.latitude', 'Latitude')}>
            <input
              type="number"
              step="0.0001"
              value={lat}
              onChange={(e) => setLat((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.era5.longitude', 'Longitude')}>
            <input
              type="number"
              step="0.0001"
              value={lon}
              onChange={(e) => setLon((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.era5.start', 'Start')}>
            <input
              type="date"
              value={start}
              onChange={(e) => setStart((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.era5.end', 'End')}>
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.era5.fetchSeries', 'Fetch ERA5 series')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.era5.fetchFailed', 'Fetch failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      {(tempSeries.length > 0 || precipSeries.length > 0) && (
        <ResultCard
          title={t('dashboard.pages.era5.resultTitle', 'ERA5 series')}
          subtitle={`${lat}, ${lon} • ${start} → ${end}`}
          badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.era5.loaded', 'Loaded') } : undefined}
        >
          {tempSeries.length > 0 && (
            <div className="mb-4">
              <h4 className="mb-2 text-sm font-semibold">{t('dashboard.pages.era5.temperature', 'Temperature (°C)')}</h4>
              <LineChart height={240} series={[{ name: 'T', data: tempSeries }]} yLabel="°C" />
            </div>
          )}
          {precipSeries.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-semibold">{t('dashboard.pages.era5.precipitation', 'Precipitation (mm)')}</h4>
              <LineChart height={240} series={[{ name: 'P', data: precipSeries, area: true }]} yLabel="mm" />
            </div>
          )}
        </ResultCard>
      )}
    </div>
  );
}