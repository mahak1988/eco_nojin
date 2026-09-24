'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { MarketMap } from '@/components/MarketMap';

export default function BazaarMapPage() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const id = (params.id as string) ?? '';
  const bazaarId = id ?? '';
  const t = useTranslations('market.bazaarMap');

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <a
              href={`/${locale}/market/bazaars/${bazaarId}`}
              className="text-sm text-ink-soft hover:text-ink underline"
            >
              ← {locale === 'fa' ? 'بازگشت به بازارچه' : 'Back to Bazaar'}
            </a>
          </nav>
          <ProvenanceStamp source="bazaar-map" label="بازارچه — نقشه">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {t('title', { id: bazaarId })}
            </h1>
          </ProvenanceStamp>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <div className="h-[600px]">
          <MarketMap bazaars={[]} locale={locale} height={600} />
        </div>
      </div>
    </main>
  );
}