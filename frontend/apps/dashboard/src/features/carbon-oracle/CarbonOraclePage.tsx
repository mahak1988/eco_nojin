import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@eco/api/mutator';
import { useMutation } from '@tanstack/react-query';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function CarbonOraclePage() {
  const { t } = useTranslation();
  const [projectId, setProjectId] = useState('demo-project');

  const issue = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post(
        `/api/v1/carbon/projects/${encodeURIComponent(projectId)}/issue`,
        {},
      );
      return data;
    },
  });

  const oracle = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.get(
        `/api/v1/carbon/projects/${encodeURIComponent(projectId)}/oracle-report`,
      );
      return data;
    },
  });

  const verify = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post(
        `/api/v1/carbon/projects/${encodeURIComponent(projectId)}/verify`,
        {},
      );
      return data;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.carbon-oracle.title', '🌱 Carbon project actions')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.carbon-oracle.subtitle', 'Issue, verify and inspect oracle reports for a carbon project.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.carbon-oracle.targetProject', 'Target project')}</h2>
        </CardHeader>
        <CardBody className="flex items-end gap-3">
          <Field label={t('dashboard.pages.carbon-oracle.projectId', 'Project ID')}>
            <input
              value={projectId}
              onChange={(e) => setProjectId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => verify.mutate()} disabled={!projectId || verify.isPending}>
              {t('dashboard.pages.carbon-oracle.verify', 'Verify')}
            </Button>
            <Button size="sm" variant="secondary" onClick={() => issue.mutate()} disabled={!projectId || issue.isPending}>
              {t('dashboard.pages.carbon-oracle.issueCredits', 'Issue credits')}
            </Button>
            <Button size="sm" onClick={() => oracle.mutate()} disabled={!projectId || oracle.isPending}>
              {t('dashboard.pages.carbon-oracle.oracleReport', 'Oracle report')}
            </Button>
          </div>
        </CardBody>
      </Card>

      {(verify.error ?? issue.error ?? oracle.error) && (
        <Alert tone="danger" title={t('dashboard.pages.carbon-oracle.actionFailed', 'Action failed')}>
          {(verify.error ?? issue.error ?? oracle.error) instanceof Error
            ? (verify.error ?? issue.error ?? oracle.error)?.message
            : t('dashboard.pages.carbon-oracle.unknownError', 'Unknown error')}
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <ResultCard title={t('dashboard.pages.carbon-oracle.verificationCard', 'Verification')} badge={verify.isSuccess ? { tone: 'success', label: t('dashboard.pages.carbon-oracle.ok', 'OK') } : undefined}>
          <RunResultView data={verify.data} loading={verify.isPending} />
        </ResultCard>
        <ResultCard title={t('dashboard.pages.carbon-oracle.issuanceCard', 'Issuance')} badge={issue.isSuccess ? { tone: 'success', label: t('dashboard.pages.carbon-oracle.ok', 'OK') } : undefined}>
          <RunResultView data={issue.data} loading={issue.isPending} />
        </ResultCard>
        <ResultCard title={t('dashboard.pages.carbon-oracle.oracleReportCard', 'Oracle report')} badge={oracle.isSuccess ? { tone: 'success', label: t('dashboard.pages.carbon-oracle.ok', 'OK') } : undefined}>
          <RunResultView data={oracle.data} loading={oracle.isPending} />
        </ResultCard>
      </div>
    </div>
  );
}