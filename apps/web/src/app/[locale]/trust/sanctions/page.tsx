'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface SanctionedEntity {
  id: string;
  name: string;
  country: string;
  type: string;
  reason: string;
  listedAt: string;
}

const SANCTIONED_ENTITIES: SanctionedEntity[] = [
  {
    id: '1',
    name: 'Entity A',
    country: 'Country X',
    type: 'Financial Institution',
    reason: 'Sanctions evasion',
    listedAt: '2024-01-15',
  },
  {
    id: '2',
    name: 'Entity B',
    country: 'Country Y',
    type: 'Individual',
    reason: 'Prohibited activities',
    listedAt: '2024-03-22',
  },
];

export default function SanctionsPage() {
  const t = useTranslations('trust.sanctions');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-4xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        <Card density="cozy" className="mb-6">
          <h2 className="font-medium text-ink mb-3">{t('policyTitle')}</h2>
          <div className="prose text-ink-soft">
            <p>{t('policyText1')}</p>
            <p className="mt-3">{t('policyText2')}</p>
            <p className="mt-3">{t('policyText3')}</p>
          </div>
        </Card>

        <Card density="cozy" className="mb-6">
          <h2 className="font-medium text-ink mb-3">{t('complianceChecklist')}</h2>
          <ul className="space-y-2 text-sm text-ink-soft">
            {t.raw('checklist')?.map((item: string, idx: number) => (
              <li key={idx} className="flex gap-2">
                <span className="text-forest">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card density="compact">
          <h2 className="font-medium text-ink mb-3">{t('sanctionedEntities')}</h2>
          <div className="grid gap-4">
            {SANCTIONED_ENTITIES.map((entity) => (
              <div key={entity.id} className="card p-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <h3 className="font-medium text-ink">{entity.name}</h3>
                    <p className="text-sm text-ink-soft">{entity.country} · {entity.type}</p>
                    <p className="text-xs text-ink-soft">Listed: {new Date(entity.listedAt).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}</p>
                  </div>
                  <ProvenanceStamp
                    source="Sanctions List"
                    verified={true}
                    timestamp={entity.listedAt}
                  />
                </div>
                <p className="mt-2 text-sm text-ink-soft">{entity.reason}</p>
              </div>
            ))}
          </div>
        </Card>

        <div className="mt-6 grid gap-4">
          <Card density="cozy" className="border-clay/40 bg-clay/5">
            <h3 className="font-medium text-ink mb-2">{t('limitsTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('limits')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-copper">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card density="cozy" className="border-forest/40 bg-forest/5">
            <h3 className="font-medium text-ink mb-2">{t('nextTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('next')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-forest">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </main>
  );
}