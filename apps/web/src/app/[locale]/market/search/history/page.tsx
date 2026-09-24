import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

interface HistoryItem {
  query: string;
  type: 'text' | 'visual' | 'semantic' | 'voice' | 'barcode';
  timestamp: string;
  results: number;
}

const MOCK_HISTORY: HistoryItem[] = [
  { query: 'پسته ارگانیک', type: 'text', timestamp: '2024-12-10 14:30', results: 12 },
  { query: 'زعفران سوپر نگین', type: 'semantic', timestamp: '2024-12-09 09:15', results: 8 },
  { query: 'badam.jpg', type: 'visual', timestamp: '2024-12-08 16:45', results: 5 },
];

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'تاریخچه جستجو', en: 'Search History' };
  const descriptions: Record<string, string> = { fa: 'مدیریت و بازبینی جستجوهای قبلی', en: 'Manage and review previous searches' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/market/search/history`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/market/search/history`, languages: { fa: `${BASE_URL}/fa/market/search/history`, en: `${BASE_URL}/en/market/search/history` } },
  };
}

export default async function HistoryPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.search.history');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-3xl px-6 pb-6 pt-2">
        <div className="flex items-center justify-between">
          <ProvenanceStamp source="Search History" label={t('provenanceLabel')} verified={true} method="Session-logged" timestamp="2024-12-10">
            <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
          </ProvenanceStamp>
          <Button variant="ghost" onClick={() => {}}>{t('clearHistory')}</Button>
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['Last 30 days', 'All search types', 'Result counts']}
          limits={['Session-only storage', 'No cross-device sync', 'Privacy-first']}
          next={['Enable export', 'Add favorites', 'Sync across devices']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-12">
        <Card density="compact">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line">
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('query')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('type')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('when')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('results')}</th>
                  <th className="text-left py-2 px-3 font-medium text-ink-soft">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_HISTORY.map((item, i) => (
                  <tr key={i} className="border-b border-line/50">
                    <td className="py-2 px-3 text-ink">{item.query}</td>
                    <td className="py-2 px-3"><span className="px-2 py-1 rounded text-xs bg-forest/10 text-forest">{item.type}</span></td>
                    <td className="py-2 px-3 text-ink-soft">{item.timestamp}</td>
                    <td className="py-2 px-3 text-ink-soft">{item.results}</td>
                    <td className="py-2 px-3"><Button variant="ghost" size="sm">{t('repeat')}</Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>
    </main>
  );
}