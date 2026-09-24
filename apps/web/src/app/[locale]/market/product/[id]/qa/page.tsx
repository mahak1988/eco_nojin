import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface QAItem {
  id: string;
  question: string;
  answer: string;
  author: string;
  date: string;
  verified: boolean;
  helpful: number;
}

const MOCK_QA: QAItem[] = [
  { id: 'q1', question: 'این پسته ارگانیک معتبر است؟', answer: 'بله، این محصول گواهی ارگانیک EU و USDA دارد.', author: 'تیم پشتیبانی', date: '2024-11-20', verified: true, helpful: 5 },
  { id: 'q2', question: 'تاریخ انقضا چقدر است؟', answer: 'این محصول تا ۱۸ ماه از تاریخ تولید قابل مصرف است.', author: 'تیم پشتیبانی', date: '2024-11-18', verified: true, helpful: 3 },
  { id: 'q3', question: 'آیا ارسال به تهران رایگان است؟', answer: 'برای سفارشات بالای ۵ میلیون تومان ارسال رایگان است.', author: 'تیم لوجیستیک', date: '2024-11-15', verified: true, helpful: 8 },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'پرسش و پاسخ', en: 'Q&A' };
  const descriptions: Record<string, string> = { fa: 'سوالات متداول و پاسخ‌های کاربران', en: 'Frequently asked questions' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/qa`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/qa`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/qa`, en: `${BASE_URL}/en/market/product/${id}/qa` } },
  };
}

export default async function QAPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.qa');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <ProvenanceStamp source="Q&A System" label={t('provenanceLabel')} verified={true} method="Community + Support" timestamp="2024-12-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
        </ProvenanceStamp>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="mb-6">
          <Button variant="primary">{t('askQuestion')}</Button>
        </div>
        <div className="space-y-4">
          {MOCK_QA.map(item => (
            <Card key={item.id} density="compact">
              <div className="mb-2">
                <span className="text-sm font-medium text-ink">{item.question}</span>
                {item.verified && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-forest/10 text-forest">{common('verifiedAnswer')}</span>}
              </div>
              <p className="text-ink-soft mb-2">{item.answer}</p>
              <div className="flex items-center justify-between text-xs text-ink-soft">
                <span>{item.author} · {new Date(item.date).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}</span>
                <span>👍 {item.helpful} {t('helpful')}</span>
              </div>
            </Card>
          ))}
        </div>
        <div className="mt-6 text-center">
          <Button variant="ghost">{t('loadMore')}</Button>
        </div>
      </section>
    </main>
  );
}