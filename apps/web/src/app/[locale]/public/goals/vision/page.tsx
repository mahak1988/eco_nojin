import { Metadata } from 'next';
import { setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type ToolRegistryDomain = { slug: string; title_fa: string; title_en: string; seq: number };

type ToolRegistry = {
  count: number;
  domains: ToolRegistryDomain[];
  categories: { domain_slug: string; count: number }[];
};

const TITLES: Record<string, string> = { fa: 'چشم‌انداز', en: 'Vision' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'دامنه‌های ثبت‌شده در رجیستری ابزار',
  en: 'The domains registered in the tool registry',
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: TITLES[locale] ?? TITLES.en,
    description: DESCRIPTIONS[locale] ?? DESCRIPTIONS.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/goals/vision`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/goals/vision`,
      languages: {
        fa: `${BASE_URL}/fa/public/goals/vision`,
        en: `${BASE_URL}/en/public/goals/vision`,
      },
    },
  };
}

export default async function VisionPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const registry = await apiGet<ToolRegistry>('/api/v1/tool-registry');
  const registryState = toDataState(
    '/api/v1/tool-registry',
    registry,
    registry.ok ? registry.data.domains.length : 0,
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <ProvenanceStamp
          source={'/api/v1/tool-registry'}
          label={title}
          verified={registry.ok}
          method={'/api/v1/tool-registry'}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/tool-registry'}</h2>
          <DataStateCard state={registryState} />
          {registryState.kind === 'ready' && registry.ok ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {registry.data.domains.map((domain) => (
                <Card key={domain.slug} density="compact">
                  <h3 className="font-medium text-ink">
                    {locale === 'fa' ? domain.title_fa : domain.title_en}
                  </h3>
                  <p className="num mt-1 text-xs text-ink-soft">{domain.slug}</p>
                  <div className="mt-2">
                    <ProvenanceStamp
                      source={'/api/v1/tool-registry'}
                      verified
                      method={domain.slug}
                    />
                  </div>
                </Card>
              ))}
            </div>
          ) : null}
          <SourceFooter state={registryState} />
        </section>
      </div>
    </main>
  );
}
