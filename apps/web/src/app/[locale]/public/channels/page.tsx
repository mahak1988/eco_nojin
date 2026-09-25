import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Channel {
  id: string;
  name: string;
  description: string;
  status: 'live' | 'beta' | 'planned';
  languages: string[];
  url: string;
}

const CHANNELS: Channel[] = [
  {
    id: 'ch1',
    name: 'Web PWA',
    description: 'Full-featured web app with offline sync',
    status: 'live',
    languages: ['fa', 'en', 'ar', 'ur', 'de', 'es', 'fr', 'hi', 'it', 'ms', 'pt', 'ru', 'zh', 'bn'],
    url: '/home',
  },
  {
    id: 'ch2',
    name: 'Mobile App',
    description: 'React Native/Expo with background sync',
    status: 'beta',
    languages: ['fa', 'en', 'ar', 'ur'],
    url: '',
  },
  {
    id: 'ch3',
    name: 'USSD',
    description: 'Feature-phone access *123#',
    status: 'planned',
    languages: ['fa', 'en', 'ar'],
    url: '',
  },
  {
    id: 'ch4',
    name: 'SMS Bot',
    description: 'Two-way SMS for alerts and queries',
    status: 'planned',
    languages: ['fa', 'en', 'ar', 'ur'],
    url: '',
  },
  {
    id: 'ch5',
    name: 'Voice IVR',
    description: 'Interactive voice response',
    status: 'planned',
    languages: ['fa', 'en', 'ar'],
    url: '',
  },
  {
    id: 'ch6',
    name: 'Telegram Bot',
    description: 'Chatbot with commands',
    status: 'planned',
    languages: ['fa', 'en', 'ar', 'ur', 'ru'],
    url: '',
  },
];

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کانال‌های دسترسی', en: 'Access Channels' };
  const descriptions: Record<string, string> = {
    fa: '۵ کانال دسترسی برای همه کاربران',
    en: '5 access channels for all users',
  };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/channels`,
      title: titles[locale] ?? titles.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/channels`,
      languages: { fa: `${BASE_URL}/fa/public/channels`, en: `${BASE_URL}/en/public/channels` },
    },
  };
}

export default async function ChannelsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.channels');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={t('provenanceLabel')}
          label={t('provenanceLabel')}
          verified={false}
          method={t('provenanceLabel')}
        >
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={t.raw('evidenceItems') as string[]}
          limits={t.raw('limitsItems') as string[]}
          next={t.raw('nextItems') as string[]}
          evidenceLabel={common('evidence')}
          limitsLabel={common('limits')}
          nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('channels')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CHANNELS.map((ch) => (
            <Card key={ch.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{ch.name}</h3>
                  <p className="text-sm text-ink-soft mt-1">{ch.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2 text-xs">
                    {ch.languages.map((l) => (
                      <span key={l} className="px-1.5 py-0.5 rounded bg-forest/10 text-forest">
                        {l}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot
                    state={ch.status === 'live' ? 'ok' : ch.status === 'beta' ? 'warn' : 'down'}
                    label={common(ch.status)}
                  />
                  {ch.id === 'ch1' ? (
                    <Link
                      href={`/${locale}/home`}
                      className="text-sm font-semibold text-[var(--color-forest)]"
                    >
                      {common('open')}
                    </Link>
                  ) : (
                    <span className="text-xs text-ink-soft">{common(ch.status)}</span>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
