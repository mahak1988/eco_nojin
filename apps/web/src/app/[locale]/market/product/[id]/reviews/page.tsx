import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface Review {
  id: string;
  author: string;
  rating: number;
  title: string;
  content: string;
  verified: boolean;
  date: string;
  helpful: number;
}

const MOCK_REVIEWS: Review[] = [
  { id: 'r1', author: 'محمد رضایی', rating: 5, title: 'عالی', content: 'کیفیت بسیار عالی، بسته‌بندی عالی', verified: true, date: '2024-11-15', helpful: 12 },
  { id: 'r2', author: 'فاطمه احمدی', rating: 4, title: 'خوب', content: 'طعم عالی، فقط ارسال کمی دیر بود', verified: true, date: '2024-11-10', helpful: 8 },
  { id: 'r3', author: 'علی محمدی', rating: 5, title: 'بهترین پسته', content: 'تا حالا بهترین پسته‌ای که خوردم', verified: false, date: '2024-11-05', helpful: 15 },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string; id: string }> }): Promise<Metadata> {
  const { locale, id } = await params;
  const titles: Record<string, string> = { fa: 'نظرات کاربران', en: 'Reviews' };
  const descriptions: Record<string, string> = { fa: 'نظرات و امتیازات خریداران', en: 'Verified buyer reviews and ratings' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/product/${id}/reviews`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/product/${id}/reviews`, languages: { fa: `${BASE_URL}/fa/market/product/${id}/reviews`, en: `${BASE_URL}/en/market/product/${id}/reviews` } },
  };
}

export default async function ReviewsPage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.product.reviews');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <nav className="mb-4 text-sm text-ink-soft">
          <a href={`/${locale}/market/product/${id}`} className="underline hover:text-ink">{common('backToProduct')}</a>
        </nav>
        <div className="flex items-center justify-between">
          <ProvenanceStamp source="Review System" label={t('provenanceLabel')} verified={true} method="Verified buyers" timestamp="2024-12-10">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title', { id })}</h1>
          </ProvenanceStamp>
          <Button variant="primary">{t('writeReview')}</Button>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-ink">{t('allReviews')}</h2>
          <span className="text-ink-soft">4.8 ★ · 24 {t('reviews')}</span>
        </div>
        <div className="space-y-4">
          {MOCK_REVIEWS.map(review => (
            <Card key={review.id} density="compact">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-ink">{review.author}</h3>
                    <span className="text-sm">{'★'.repeat(review.rating)}</span>
                    {review.verified && <span className="px-2 py-0.5 rounded text-xs bg-forest/10 text-forest">{common('verifiedBuyer')}</span>}
                  </div>
                  <h4 className="font-medium text-ink mt-1">{review.title}</h4>
                  <p className="text-sm text-ink-soft mt-1">{review.content}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-ink-soft">
                    <span>{new Date(review.date).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US')}</span>
                    <span>👍 {review.helpful} {t('helpful')}</span>
                  </div>
                </div>
                <Button variant="ghost" size="sm">{t('markHelpful')}</Button>
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