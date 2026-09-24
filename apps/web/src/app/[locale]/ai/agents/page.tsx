'use client';

import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const AGENTS = [
  {
    id: 'irrigation',
    icon: '💧',
    titleKey: 'agents.irrigation.title',
    descriptionKey: 'agents.irrigation.description',
    capabilitiesKey: 'agents.irrigation.capabilities',
  },
  {
    id: 'soil',
    icon: '🌱',
    titleKey: 'agents.soil.title',
    descriptionKey: 'agents.soil.description',
    capabilitiesKey: 'agents.soil.capabilities',
  },
  {
    id: 'carbon',
    icon: '🌿',
    titleKey: 'agents.carbon.title',
    descriptionKey: 'agents.carbon.description',
    capabilitiesKey: 'agents.carbon.capabilities',
  },
];

export default function AgentsPage() {
  const t = useTranslations('ai.agents');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1];

  const navigate = (href: string) => router.push(href);

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10 text-center">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 max-w-2xl mx-auto text-ink-soft">{t('lead')}</p>
        </header>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {AGENTS.map((agent) => (
            <Card key={agent.id} density="cozy" className="flex flex-col h-full">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl" aria-hidden="true">{agent.icon}</span>
                <h2 className="text-xl font-semibold text-ink">{t(agent.titleKey)}</h2>
              </div>
              <p className="text-ink-soft mb-4">{t(agent.descriptionKey)}</p>
              <ul className="mb-6 flex-1 space-y-2 text-sm text-ink">
                {t.raw(agent.capabilitiesKey)?.map((cap: string, idx: number) => (
                  <li key={idx} className="flex gap-2">
                    <span className="text-forest">✓</span>
                    <span>{cap}</span>
                  </li>
                ))}
              </ul>
              <Button variant="primary" className="w-full" onClick={() => navigate(`/${locale}/ai/assistant`)}>
                {t('tryAgent', { agent: t(agent.titleKey) })}
              </Button>
            </Card>
          ))}
        </div>

        <section className="mt-12" aria-labelledby="cta-heading">
          <h2 id="cta-heading" className="sr-only">{t('ctaTitle')}</h2>
          <Card density="cozy" className="text-center">
            <h3 className="text-lg font-medium text-ink mb-2">{t('ctaTitle')}</h3>
            <p className="text-ink-soft mb-4">{t('ctaDescription')}</p>
            <Button variant="primary" size="lg" onClick={() => navigate(`/${locale}/ai/assistant`)}>
              {t('ctaButton')}
            </Button>
          </Card>
        </section>
      </div>
    </main>
  );
}