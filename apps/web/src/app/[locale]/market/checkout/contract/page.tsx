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
  const titles: Record<string, string> = { fa: 'قرارداد و شرایط', en: 'Contract & Terms' };
  const descriptions: Record<string, string> = { fa: 'مشاهده و پذیرش قرارداد اسکرو', en: 'View and accept escrow contract' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/checkout/contract`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/checkout/contract`, languages: { fa: `${BASE_URL}/fa/market/checkout/contract`, en: `${BASE_URL}/en/market/checkout/contract` } },
  };
}

export default async function ContractPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.checkout.contract');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="Legal Registry" label={t('provenanceLabel')} verified={true} method="Version-controlled" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Version-controlled', '14-language sync', 'Legal review per release']}
          limits={['Not legal advice', 'Jurisdiction-specific gaps', 'Enforceability varies by region']}
          next={['Add automated compliance', 'Enable diff viewer', 'Integrate e-signature']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="cozy">
          <div className="prose max-w-none text-ink space-y-4">
            <h3 className="font-semibold text-xl mb-2">{t('contractTitle')}</h3>
            <p className="text-ink-soft">{t('contractBody')}</p>
            <div className="border-t border-line my-4"></div>
            <h4 className="font-semibold">{t('keyClauses')}</h4>
            <ul className="list-disc list-inside space-y-1 text-ink-soft">
              <li>{t('clause1')}</li>
              <li>{t('clause2')}</li>
              <li>{t('clause3')}</li>
              <li>{t('clause4')}</li>
              <li>{t('clause5')}</li>
            </ul>
          </div>
          <div className="mt-4">
            <ProvenanceStamp source="Legal Registry" verified={true} method="Git-signed" timestamp="2024-12-01" label={t('provenanceLabel')} />
          </div>
        </Card>

        <div className="mt-6 flex gap-3">
          <Button variant="ghost" onClick={() => window.location.href = `/${locale}/market/checkout/escrow-setup`}>
            {common('back')}
          </Button>
          <Button variant="primary" className="flex-1" onClick={() => window.location.href = `/${locale}/market/checkout/transaction-key`}>
            {t('acceptAndContinue')}
          </Button>
        </div>
      </section>
    </main>
  );
}