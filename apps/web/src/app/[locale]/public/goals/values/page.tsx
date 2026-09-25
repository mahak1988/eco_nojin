import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

type UssdStatus = {
  status: string;
  ussd_code: string;
  requires_gateway: boolean;
  blocked_by_upstream: boolean;
  notes: string;
};

type VoiceStatus = { status: string; requires_gateway: boolean; available_languages: number };

const TITLES: Record<string, string> = { fa: 'ارزش‌ها', en: 'Values' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'وضعیت واقعی دسترسی بدون گوشی هوشمند از مسیر USSD و صوت',
  en: 'The real feature-phone access status from the USSD and voice routes',
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
      url: `${BASE_URL}/${locale}/public/goals/values`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/goals/values`,
      languages: {
        fa: `${BASE_URL}/fa/public/goals/values`,
        en: `${BASE_URL}/en/public/goals/values`,
      },
    },
  };
}

export default async function ValuesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const common = await getTranslations('common');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const [ussd, voice] = await Promise.all([
    apiGet<UssdStatus>('/api/v1/ussd/status'),
    apiGet<VoiceStatus>('/api/v1/voice/status'),
  ]);
  const ussdState = toDataState('/api/v1/ussd/status', ussd, ussd.ok ? 1 : 0);
  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <ProvenanceStamp
          source={'/api/v1/ussd/status'}
          label={title}
          verified={ussd.ok}
          method={'/api/v1/ussd/status'}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>

        <section className="mt-8">
          <h2 className="text-xl font-semibold text-ink mb-4">{'/api/v1/ussd/status'}</h2>
          <DataStateCard state={ussdState} />
          {ussdState.kind === 'ready' && ussd.ok ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <Card density="compact">
                <p className="num font-mono text-2xl text-ink">{ussd.data.ussd_code}</p>
                <p className="mt-1 text-sm text-ink-soft">{ussd.data.status}</p>
                <p className="mt-1 text-xs text-ink-soft">{ussd.data.notes}</p>
                <div className="mt-2">
                  <ProvenanceStamp
                    source={'/api/v1/ussd/status'}
                    verified
                    method={'/api/v1/ussd/status'}
                  />
                </div>
              </Card>
              {voice.ok ? (
                <Card density="compact">
                  <p className="text-sm text-ink">{voice.data.status}</p>
                  <p className="num mt-1 text-2xl text-ink">{voice.data.available_languages}</p>
                  <p className="mt-1 text-xs text-ink-soft">
                    {voice.data.requires_gateway ? status('unavailable') : common('live')}
                  </p>
                  <div className="mt-2">
                    <ProvenanceStamp
                      source={'/api/v1/voice/status'}
                      verified
                      method={'/api/v1/voice/status'}
                    />
                  </div>
                </Card>
              ) : null}
            </div>
          ) : null}
          <SourceFooter state={ussdState} />
        </section>
      </div>
    </main>
  );
}
