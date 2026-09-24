import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/StatusDot';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Workshop {
  id: string;
  title: string;
  date: string;
  location: string;
  format: 'online' | 'hybrid' | 'in-person';
  language: string[];
  seats: number;
  registered: number;
  status: 'open' | 'full' | 'completed';
  source: string;
}

const MOCK_WORKSHOPS: Workshop[] = [
  { id: 'w1', title: 'Participatory Land Mapping Workshop', date: '2025-02-15', location: 'Tehran, Iran', format: 'hybrid', language: ['fa', 'en'], seats: 30, registered: 18, status: 'open', source: 'FAO Iran' },
  { id: 'w2', title: 'Carbon Farming Field Day', date: '2025-03-20', location: 'Kerman, Iran', format: 'in-person', language: ['fa'], seats: 25, registered: 25, status: 'full', source: 'Kerman Coop' },
  { id: 'w3', title: 'HydroMa Model Calibration Training', date: '2025-04-10', location: 'Online', format: 'online', language: ['en', 'es', 'fr'], seats: 50, registered: 32, status: 'open', source: 'HydroMa Academy' },
  { id: 'w4', title: 'Advanced MRV Techniques', date: '2024-11-15', location: 'Dubai, UAE', format: 'hybrid', language: ['en', 'ar'], seats: 40, registered: 40, status: 'completed', source: 'ICROA' },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کارگاه‌های حضوری', en: 'Workshops' };
  const descriptions: Record<string, string> = { fa: 'تقویم کارگاه‌های تخصصی و رویدادها', en: 'Specialized workshops and events calendar' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/education/workshops`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/education/workshops`, languages: { fa: `${BASE_URL}/fa/public/education/workshops`, en: `${BASE_URL}/en/public/education/workshops` } },
  };
}

export default async function WorkshopsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.education.workshops');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Workshop Registry" label={t('provenanceLabel')} verified={true} method="Partner-curated" timestamp="2024-12-10">
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
          evidence={['Partner organizations', 'Hands-on exercises', 'Certificate of attendance']}
          limits={['Limited seats', 'Travel costs for in-person', 'Timezone challenges for hybrid']}
          next={['Add recording access', 'Enable waitlist', 'Regional hub partnerships']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('schedule')}</h2>
        <div className="grid gap-4">
          {MOCK_WORKSHOPS.map(ws => (
            <Card key={ws.id} density="compact">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="font-medium text-ink">{ws.title}</h3>
                  <p className="text-sm text-ink-soft mt-1">{ws.date} · {ws.location} · {ws.format}</p>
                  <div className="flex flex-wrap gap-2 mt-2 text-xs">
                    {ws.language.map(l => <span key={l} className="px-2 py-1 rounded bg-forest/10 text-forest">{l}</span>)}
                    <span className="px-2 py-1 rounded bg-clay/10 text-clay">{ws.registered}/{ws.seats}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusDot state={ws.status === 'open' ? 'ok' : ws.status === 'full' ? 'warn' : 'down'} label={common(ws.status)} />
                  <ProvenanceStamp source={ws.source} verified={true} label={ws.format} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}