'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface Cookbook {
  id: string;
  title: string;
  description: string;
  language: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  tags: string[];
  codeUrl: string;
}

const COOKBOOKS: Cookbook[] = [
  {
    id: 'create-order',
    title: 'Create a Marketplace Order',
    description: 'Step-by-step guide to creating an order with escrow',
    language: 'TypeScript',
    difficulty: 'beginner',
    tags: ['marketplace', 'escrow', 'orders'],
    codeUrl: 'https://github.com/eco-nojin/cookbooks/tree/main/create-order',
  },
  {
    id: 'ai-assistant',
    title: 'Integrate AI Assistant',
    description: 'How to add the AI assistant chat to your application',
    language: 'TypeScript',
    difficulty: 'intermediate',
    tags: ['ai', 'chat', 'rag'],
    codeUrl: 'https://github.com/eco-nojin/cookbooks/tree/main/ai-assistant',
  },
  {
    id: 'webhook-setup',
    title: 'Set Up Webhook Endpoint',
    description: 'Configure and verify webhook signatures',
    language: 'Python',
    difficulty: 'beginner',
    tags: ['webhooks', 'security'],
    codeUrl: 'https://github.com/eco-nojin/cookbooks/tree/main/webhook-setup',
  },
  {
    id: 'carbon-credits',
    title: 'Query Carbon Credits',
    description: 'Fetch and display carbon credit data from the registry',
    language: 'TypeScript',
    difficulty: 'intermediate',
    tags: ['carbon', 'registry', 'blockchain'],
    codeUrl: 'https://github.com/eco-nojin/cookbooks/tree/main/carbon-credits',
  },
  {
    id: 'bazaar-creation',
    title: 'Establish a Bazaar',
    description: 'Complete 10-step bazaar establishment flow',
    language: 'TypeScript',
    difficulty: 'advanced',
    tags: ['bazaar', 'multisig', 'governance'],
    codeUrl: 'https://github.com/eco-nojin/cookbooks/tree/main/bazaar-creation',
  },
];

const difficultyColors = {
  beginner: 'text-forest bg-forest/10',
  intermediate: 'text-water bg-water/10',
  advanced: 'text-copper bg-copper/10',
};

export default function CookbooksPage() {
  const t = useTranslations('developers.cookbooks');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        <div className="grid gap-6">
          {COOKBOOKS.map((cookbook) => (
            <Card key={cookbook.id} density="cozy">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <h3 className="text-xl font-semibold text-ink">{cookbook.title}</h3>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${difficultyColors[cookbook.difficulty]}`}>
                      {t(`difficulty.${cookbook.difficulty}`)}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs bg-water/10 text-water font-mono">
                      {cookbook.language}
                    </span>
                  </div>
                  <p className="text-ink-soft mb-4">{cookbook.description}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {cookbook.tags.map((tag) => (
                      <span key={tag} className="px-2 py-0.5 rounded text-xs bg-surface-2 border border-line text-ink-soft">
                        #{tag}
                      </span>
                    ))}
                  </div>
                  <a
                    href={cookbook.codeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-water hover:underline"
                  >
                    {t('viewCode')} →
                  </a>
                </div>
                <Button variant="secondary" size="sm" onClick={() => navigator.clipboard.writeText(cookbook.codeUrl)}>
                  {t('copyUrl')}
                </Button>
              </div>
              <ProvenanceStamp source="Cookbook Registry" verified={true} method="Community reviewed" />
            </Card>
          ))}
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-3">{t('contribute')}</h2>
          <p className="text-sm text-ink-soft mb-4">{t('contributeDesc')}</p>
          <a
            href="https://github.com/eco-nojin/cookbooks"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-water hover:underline"
          >
            {t('contributeLink')}
          </a>
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