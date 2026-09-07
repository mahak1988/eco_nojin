import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@eco/api/mutator';
import { Alert, Badge, Button, Card, CardBody, CardHeader, EmptyState, Input, Spinner } from '@eco/ui';
import { StatCard3D } from '@eco/ui';
import { formatNumber } from '@eco/utils';

type DroughtResult = {
  spi?: number;
  status?: string;
  severity?: string;
  category?: string;
  [key: string]: unknown;
};

export function ClimatePage() {
  const { t } = useTranslation();
  const [lat, setLat] = useState('35.6892');
  const [lon, setLon] = useState('51.3890');

  const drought = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<DroughtResult>('/climate/drought', {
        latitude: Number(lat),
        longitude: Number(lon),
      });
      return data;
    },
  });

  const value = drought.data;

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.climate.title', '🌤️ Climate analysis')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.climate.subtitle', 'Drought, ERA5 reanalysis, and climate projection workflows via')}{' '}
          <code className="rounded bg-surface-muted px-1">/climate/*</code>
          {t('dashboard.pages.climate.subtitlePeriod', '.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.climate.droughtAnalysis', 'Drought analysis (SPI)')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-3">
          <Field label={t('dashboard.pages.climate.latitude', 'Latitude')}>
            <Input
              type="number"
              step="0.0001"
              value={lat}
              onChange={(e) => setLat((e.target as HTMLInputElement).value)}
            />
          </Field>
          <Field label={t('dashboard.pages.climate.longitude', 'Longitude')}>
            <Input
              type="number"
              step="0.0001"
              value={lon}
              onChange={(e) => setLon((e.target as HTMLInputElement).value)}
            />
          </Field>
          <div className="flex items-end">
            <Button onClick={() => drought.mutate()} disabled={drought.isPending}>
              {drought.isPending && <Spinner size="sm" tone="inverse" />}
              {t('dashboard.pages.climate.analyzeDrought', 'Analyze drought')}
            </Button>
          </div>
        </CardBody>
      </Card>

      {drought.error && (
        <Alert tone="danger" title={t('dashboard.pages.climate.droughtFailed', 'Drought analysis failed')}>
          {(drought.error as Error).message}
        </Alert>
      )}

      {value && (
        <section className="grid gap-4 md:grid-cols-3">
          <StatCard3D label={t('dashboard.pages.climate.spiIndex', 'SPI index')} value={formatNumber(value.spi ?? NaN, { decimals: 2 })} icon="📈" />
          <StatCard3D label={t('dashboard.pages.climate.status', 'Status')} value={value.status ?? value.category ?? '—'} icon="📊" />
          <StatCard3D label={t('dashboard.pages.climate.severity', 'Severity')} value={value.severity ?? '—'} icon="⚠️" />
        </section>
      )}

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold">{t('dashboard.pages.climate.availableWorkflows', 'Available workflows')}</h3>
          </CardHeader>
          <CardBody className="grid grid-cols-2 gap-2 text-sm">
            <Badge tone="info" variant="soft">{t('dashboard.pages.climate.workflowDrought', 'Drought (SPI)')}</Badge>
            <Badge tone="info" variant="soft">{t('dashboard.pages.climate.workflowEra5', 'ERA5 reanalysis')}</Badge>
            <Badge tone="info" variant="soft">{t('dashboard.pages.climate.workflowRcp', 'RCP projections')}</Badge>
            <Badge tone="info" variant="soft">{t('dashboard.pages.climate.workflowBayesian', 'Bayesian calibration')}</Badge>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold">{t('dashboard.pages.climate.latestSnapshot', 'Latest snapshot')}</h3>
          </CardHeader>
          <CardBody className="text-sm">
            {!value ? (
              <EmptyState
                title={t('dashboard.pages.climate.noDataYet', 'No data yet')}
                description={t('dashboard.pages.climate.noDataDescription', 'Run a drought analysis to populate the snapshot.')}
              />
            ) : (
              <pre className="overflow-auto text-[11px] text-ink">
                {JSON.stringify(value, null, 2)}
              </pre>
            )}
          </CardBody>
        </Card>
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-muted">
      {label}
      {children}
    </label>
  );
}

function Stat({ label, value, icon }: { label: string; value: number | string; icon: string }) {
  return (
    <Card>
      <CardBody className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="text-xs uppercase tracking-wide text-ink-muted">{label}</div>
          <div className="text-xl font-semibold text-brand-700">{value}</div>
        </div>
      </CardBody>
    </Card>
  );
}