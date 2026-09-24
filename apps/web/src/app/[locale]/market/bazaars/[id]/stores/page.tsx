'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

export default function BazaarStoresPage() {
  const params = useParams();
  const { locale, id } = params;
  const bazaarId = (Array.isArray(id) ? id[0] : id) ?? '';
  const t = useTranslations('market.bazaarStores');

  const mockStores = [
    { id: 's001', name: 'فروشگاه آویز', producer: 'تعاونی کرمان', products: 12, status: 'active' },
    { id: 's002', name: 'زعفران طلایی', producer: 'مزارع خراسان', products: 8, status: 'active' },
    { id: 's003', name: 'عسل طبیعی', producer: 'معدن‌سازی گیلان', products: 15, status: 'pending' },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-6">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <nav className="mb-4">
              <a
                href={`/${locale}/market/bazaars/${bazaarId}`}
                className="text-sm text-ink-soft hover:text-ink underline"
              >
                ← {locale === 'fa' ? 'بازگشت به بازارچه' : 'Back to Bazaar'}
              </a>
            </nav>
            <ProvenanceStamp source="bazaar-stores" label="بازارچه — فروشگاه‌ها">
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
                {t('title', { id: bazaarId })}
              </h1>
            </ProvenanceStamp>
          </div>
          <Link href={`/${locale}/market/stores/create?bazaar=${bazaarId}`}>
            <Button>{t('createStore')}</Button>
          </Link>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {mockStores.map(store => (
            <Card key={store.id} className="p-4">
              <h3 className="font-medium text-ink">{store.name}</h3>
              <p className="text-sm text-ink-soft">{store.producer}</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-sm text-ink">{store.products} {t('products')}</span>
                <span className={`text-xs px-2 py-1 rounded ${
                  store.status === 'active' ? 'bg-success/10 text-success' : 'bg-amber/10 text-amber'
                }`}>
                  {store.status}
                </span>
              </div>
              <Link href={`/${locale}/market/stores/${store.id}`} className="mt-3 block text-sm text-primary hover:underline">
                {t('viewStore')}
              </Link>
            </Card>
          ))}
        </div>

        {mockStores.length === 0 && (
          <Card className="text-center py-8">
            <p className="text-ink-soft">{t('noStores')}</p>
            <Link href={`/${locale}/market/stores/create?bazaar=${id}`} className="mt-4 inline-block">
              <Button>{t('createFirstStore')}</Button>
            </Link>
          </Card>
        )}
      </div>
    </main>
  );
}