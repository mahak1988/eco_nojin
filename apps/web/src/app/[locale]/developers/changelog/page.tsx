'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface ChangelogEntry {
  version: string;
  date: string;
  type: 'added' | 'changed' | 'deprecated' | 'removed' | 'fixed' | 'security';
  changes: string[];
}

const CHANGELOG: ChangelogEntry[] = [
  {
    version: '1.2.0',
    date: '2024-12-15',
    type: 'added',
    changes: [
      'Added webhooks for carbon credit issuance',
      'New SDK method for batch order creation',
      'Support for PQ digital signatures in bazaar establishment',
    ],
  },
  {
    version: '1.1.0',
    date: '2024-10-01',
    type: 'added',
    changes: [
      'Added AI voice interface endpoint',
      'New marketplace stats endpoint',
      'Rate limit headers in all responses',
    ],
  },
  {
    version: '1.0.0',
    date: '2024-07-01',
    type: 'added',
    changes: [
      'Initial public API release',
      'Platform, marketplace, and trust endpoints',
      'OpenAPI 3.1 specification',
    ],
  },
];

const typeLabels = {
  added: 'Added',
  changed: 'Changed',
  deprecated: 'Deprecated',
  removed: 'Removed',
  fixed: 'Fixed',
  security: 'Security',
};

const typeColors = {
  added: 'text-forest bg-forest/10',
  changed: 'text-water bg-water/10',
  deprecated: 'text-copper bg-copper/10',
  removed: 'text-clay bg-clay/10',
  fixed: 'text-amber bg-amber/10',
  security: 'text-red bg-red/10',
};

export default function ChangelogPage() {
  const t = useTranslations('developers.changelog');
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

        <div className="space-y-6">
          {CHANGELOG.map((entry) => (
            <Card key={entry.version} density="cozy">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-ink">{t('versionLabel')} {entry.version}</h2>
                  <p className="text-sm text-ink-soft">
                    {new Date(entry.date).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${typeColors[entry.type]}`}>
                  {typeLabels[entry.type]}
                </span>
              </div>
              <ul className="space-y-2">
                {entry.changes.map((change, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-ink-soft">
                    <span className="text-forest">•</span>
                    <span>{change}</span>
                  </li>
                ))}
              </ul>
              <ProvenanceStamp source="API Changelog" verified={true} timestamp={entry.date} />
            </Card>
          ))}
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-3">{t('subscription')}</h2>
          <p className="text-sm text-ink-soft mb-4">{t('subscriptionDesc')}</p>
          <form className="flex gap-2">
            <input
              type="email"
              placeholder={t('emailPlaceholder')}
              className="flex-1 px-4 py-2 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
            />
            <button type="submit" className="px-4 py-2 bg-forest text-paper rounded-md font-medium hover:bg-forest/90 transition-colors">
              {t('subscribe')}
            </button>
          </form>
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