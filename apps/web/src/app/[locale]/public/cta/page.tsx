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
  const titles: Record<string, string> = { fa: 'دعوت به اقدام', en: 'Call to Action' };
  const descriptions: Record<string, string> = { fa: 'CTAهای اصلی برای ورود به اکوسیستم', en: 'Primary CTAs to enter the ecosystem' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/cta`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/cta`, languages: { fa: `${BASE_URL}/fa/public/cta`, en: `${BASE_URL}/en/public/cta` } },
  };
}

export default async function CTAPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.cta');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="UX Strategy" label={t('provenanceLabel')} verified={true} method="A/B tested" timestamp="2024-12-01">
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
          evidence={['User journey mapping', 'Conversion funnel analysis', 'Accessibility audit']}
          limits={['Mobile UX needs refinement', 'Offline CTA sync pending', 'Regional CTA variants WIP']}
          next={['Add smart CTA routing', 'Enable deep linking', 'Personalize by role']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('primaryCTAs')}</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta1_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta1_desc')}</p>
            <Button variant="primary" size="lg" onClick={() => window.location.href = `/${locale}/market`}>{t('cta1_action')}</Button>
          </Card>
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta2_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta2_desc')}</p>
            <Button variant="secondary" size="lg" onClick={() => window.location.href = `/${locale}/hydroma`}>{t('cta2_action')}</Button>
          </Card>
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta3_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta3_desc')}</p>
            <Button variant="ghost" size="lg" onClick={() => window.location.href = `/${locale}/public/education/library`}>{t('cta3_action')}</Button>
          </Card>
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta4_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta4_desc')}</p>
            <Button variant="ghost" size="lg" onClick={() => window.location.href = `/${locale}/public/policy/terms`}>{t('cta4_action')}</Button>
          </Card>
        </div>
      </section>
    </main>
  );
}