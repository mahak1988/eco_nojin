import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface WarrantyInfo {
  id: string;
  title: { fa: string; en: string };
  description: { fa: string; en: string };
  duration: string;
  coverage: string[];
  claimProcess: string;
  status: 'active' | 'conditional';
}

const MOCK_WARRANTY: WarrantyInfo = {
  id: 'w1',
  title: { fa: 'گارانتی کیفیت', en: 'Quality Warranty' },
  description: { fa: 'این محصول تحت گارانتی کیفیت ۱۲ ماهه است.', en: 'This product is covered by a 12-month quality warranty.' },
  duration: '12 months',
  coverage: ['مواد اولیه', 'بسته‌بندی', 'طعم و بوی طبیعی'],
  claimProcess: 'برای ثبت درخواست گارانتی، لطفاً از طریق سامانه تیکت یا تماس با پشتیبانی اقدام کنید.',
  status: 'active',
};

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'گارانتی و مرجوعی', en: 'Warranty & Returns' };
  const descriptions: Record<string, string> = { fa: 'شرایط گارانتی و فرآیند مرجوعی', en: 'Warranty terms and return process' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/warranty`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/warranty`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/warranty`, en: `${BASE_URL}/en/market/product/${id}/warranty` } },
  };
}

export default async function WarrantyPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  const loc = locale as string;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.warranty');
  const common = await getTranslations('common');
  const warranty = MOCK_WARRANTY;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Warranty Registry" label={t('provenanceLabel')} verified={true} method="Producer-declared" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <Card density="cozy">
          <h2 className="font-semibold text-ink mb-4">{(warranty.title as Record<string, string>)[loc] ?? warranty.title.fa}</h2>
          <p className="text-ink-soft mb-4">{(warranty.description as Record<string, string>)[loc] ?? warranty.description.fa}</p>
          
          <div className="grid gap-4 mb-6">
            <div>
              <span className="text-xs text-ink-soft">{t('duration')}</span>
              <p className="font-medium text-ink">{warranty.duration}</p>
            </div>
            <div>
              <span className="text-xs text-ink-soft">{t('status')}</span>
              <span className="px-2 py-1 rounded text-sm font-medium bg-forest/10 text-forest">{t('active')}</span>
            </div>
          </div>

          <h3 className="font-semibold text-ink mb-3">{t('coverage')}</h3>
          <ul className="space-y-1">
            {warranty.coverage.map((item, i) => (
              <li key={i} className="flex items-center gap-2 text-ink-soft">
                <span className="text-forest">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>

          <h3 className="font-semibold text-ink mt-6 mb-3">{t('claimProcess')}</h3>
          <p className="text-ink-soft">{warranty.claimProcess}</p>

          <div className="mt-6 flex gap-3">
            <Button variant="primary">{t('fileClaim')}</Button>
            <Button variant="ghost">{t('viewTerms')}</Button>
          </div>
        </Card>

        <div className="mt-4">
          <ProvenanceStamp source="Warranty Registry" verified={true} method="Producer-declared" label={t('provenanceLabel')} />
        </div>
      </section>
    </main>
  );
}