'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface SdkInfo {
  name: string;
  language: string;
  version: string;
  description: string;
  npmUrl: string;
  githubUrl: string;
  installCmd: string;
}

const SDKS: SdkInfo[] = [
  {
    name: '@eco/sdk-typescript',
    language: 'TypeScript',
    version: '1.2.0',
    description: 'Full-featured TypeScript SDK with React hooks',
    npmUrl: 'https://npmjs.com/package/@eco/sdk-typescript',
    githubUrl: 'https://github.com/eco-nojin/sdk-typescript',
    installCmd: 'npm install @eco/sdk-typescript',
  },
  {
    name: 'eco-sdk-python',
    language: 'Python',
    version: '1.1.0',
    description: 'Python SDK for backend integrations and data science',
    npmUrl: 'https://pypi.org/project/eco-sdk-python/',
    githubUrl: 'https://github.com/eco-nojin/sdk-python',
    installCmd: 'pip install eco-sdk-python',
  },
  {
    name: '@eco/sdk-go',
    language: 'Go',
    version: '1.0.0',
    description: 'Go SDK for high-performance services',
    npmUrl: 'https://pkg.go.dev/github.com/eco-nojin/sdk-go',
    githubUrl: 'https://github.com/eco-nojin/sdk-go',
    installCmd: 'go get github.com/eco-nojin/sdk-go',
  },
];

export default function SdksPage() {
  const t = useTranslations('developers.sdks');
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
          {SDKS.map((sdk) => (
            <Card key={sdk.name} density="cozy">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold text-ink">{sdk.name}</h3>
                    <span className="px-2 py-0.5 rounded text-xs bg-water/10 text-water font-mono">
                      {sdk.language}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs bg-forest/10 text-forest font-mono">
                      v{sdk.version}
                    </span>
                  </div>
                  <p className="text-ink-soft mb-4">{sdk.description}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    <a href={sdk.npmUrl} target="_blank" rel="noopener noreferrer" className="text-sm text-water hover:underline">
                      {t('npmRegistry')}
                    </a>
                    <span className="text-ink-soft">·</span>
                    <a href={sdk.githubUrl} target="_blank" rel="noopener noreferrer" className="text-sm text-water hover:underline">
                      {t('githubRepo')}
                    </a>
                  </div>
                  <pre className="bg-surface-2 border border-line rounded-md p-3 text-xs font-mono overflow-x-auto text-ink">
                    {sdk.installCmd}
                  </pre>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <Button variant="secondary" size="sm" onClick={() => navigator.clipboard.writeText(sdk.installCmd)}>
                    {t('copyInstallCmd')}
                  </Button>
                </div>
              </div>
              <ProvenanceStamp source="SDK Registry" verified={true} method="Automated publish" />
            </Card>
          ))}
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-3">{t('quickStart')}</h2>
          <p className="text-sm text-ink-soft mb-4">{t('quickStartDesc')}</p>
          <pre className="bg-surface-2 border border-line rounded-md p-4 text-xs font-mono overflow-x-auto text-ink">
            {t('quickStartExample')}
          </pre>
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