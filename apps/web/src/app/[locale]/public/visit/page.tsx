import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'بازدید میدانی', en: 'Field Visit' };
  const descriptions: Record<string, string> = { fa: 'راهنمای بازدید از سایت‌های پایلوت', en: 'Pilot site visit guide' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/visit`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/visit`, languages: { fa: `${BASE_URL}/fa/public/visit`, en: `${BASE_URL}/en/public/visit` } },
  };
}

export default async function VisitPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.visit');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Field Protocol" label={t('provenanceLabel')} verified={true} method="Pilot-tested" timestamp="2024-12-01">
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
          evidence={['3 pilot villages', 'Soil/Water/Carbon protocols', 'Community consent forms']}
          limits={['Seasonal access limits', 'Security clearance needed', 'Translation of forms pending']}
          next={['Add VR site tour', 'Schedule quarterly visits', 'Publish visit reports']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('visitSteps')}</h2>
        <div className="grid gap-4">
          {[
            { step: 1, title: t('s1_title'), desc: t('s1_desc') },
            { step: 2, title: t('s2_title'), desc: t('s2_desc') },
            { step: 3, title: t('s3_title'), desc: t('s3_desc') },
            { step: 4, title: t('s4_title'), desc: t('s4_desc') },
          ].map(s => (
            <Card key={s.step} density="compact">
              <div className="flex gap-4">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-forest/10 text-forest font-bold">{s.step}</span>
                <div>
                  <h3 className="font-medium text-ink">{s.title}</h3>
                  <p className="text-sm text-ink-soft">{s.desc}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
        <Button variant="primary" className="mt-6">{t('scheduleVisit')}</Button>
      </section>
    </main>
  );
}