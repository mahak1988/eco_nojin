import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Channel {
  id: string;
  name: string;
  description: string;
  status: 'live' | 'beta' | 'planned';
  languages: string[];
  url: string;
}

const MOCK_CHANNELS: Channel[] = [
  { id: 'ch1', name: 'Web PWA', description: 'Full-featured web app with offline sync', status: 'live', languages: ['fa','en','ar','ur','de','es','fr','hi','it','ms','pt','ru','zh','bn'], url: '/home' },
  { id: 'ch2', name: 'Mobile App', description: 'React Native/Expo with background sync', status: 'beta', languages: ['fa','en','ar','ur'], url: '/mobile' },
  { id: 'ch3', name: 'USSD', description: 'Feature phone access *123#', status: 'live', languages: ['fa','en','ar'], url: '/ussd' },
  { id: 'ch4', name: 'SMS Bot', description: 'Two-way SMS for alerts/queries', status: 'live', languages: ['fa','en','ar','ur'], url: '/sms' },
  { id: 'ch5', name: 'Voice IVR', description: 'Interactive voice response', status: 'planned', languages: ['fa','en','ar'], url: '/voice' },
  { id: 'ch6', name: 'Telegram Bot', description: 'Chatbot with commands', status: 'live', languages: ['fa','en','ar','ur','ru'], url: '/telegram' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کانال‌های دسترسی', en: 'Access Channels' };
  const descriptions: Record<string, string> = { fa: '۵ کانال دسترسی برای همه کاربران', en: '5 access channels for all users' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/channels`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/channels`, languages: { fa: `${BASE_URL}/fa/public/channels`, en: `${BASE_URL}/en/public/channels` } },
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
        <ProvenanceStamp source="Channel Registry" label={t('provenanceLabel')} verified={true} method="Deploy-tracked" timestamp="2024-12-10">
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
          evidence={['Inclusive design', 'Offline-first', '14 languages']}
          limits={['Voice IVR not live', 'Mobile app beta', 'USSD character limits']}
          next={['Launch Voice IVR', 'Mobile app GA', 'Add WhatsApp Business']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('channels')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MOCK_CHANNELS.map(ch => (
            <Card key={ch.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{ch.name}</h3>
                  <p className="text-sm text-ink-soft mt-1">{ch.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2 text-xs">
                    {ch.languages.map(l => <span key={l} className="px-1.5 py-0.5 rounded bg-forest/10 text-forest">{l}</span>)}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={ch.status === 'live' ? 'ok' : ch.status === 'beta' ? 'warn' : 'down'} label={common(ch.status)} />
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = ch.url}>{common('open')}</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}