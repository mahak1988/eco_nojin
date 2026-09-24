'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';

interface BazaarProduct {
  id: string;
  name: string;
  producer: string;
  price: number;
  unit: string;
  stock: number;
  organic: boolean;
  verified: boolean;
  category: string;
  rating: number;
}

interface StoreInfo {
  id: string;
  name: string;
  producer: string;
  description: string;
  location: string;
  members: number;
  established: string;
  signature: string;
}

const MOCK_BAZAAR: StoreInfo = {
  id: 'b001',
  name: 'مرکز بازارچه نهادی مرکزی',
  producer: 'هیئت مدیره بازارچه مرکزی',
  description:
    'بازارچه نهادی مرکزی شامل ۴۲ فروشگاه و ۸ بازار فرعی در مناطق روستایی استان خراسان. هیئت ۵ نفره با امضای دیجیتال PQ مدیریت می‌شود.',
  location: 'خراسان رضوی، ایران',
  members: 42,
  established: '2025-06-15',
  signature: 'DILITHIUM2+ED25519',
};

const MOCK_PRODUCTS: BazaarProduct[] = [
  { id: 'p001', name: 'Organic Pistachio Kernels', producer: 'Kerman Cooperative', price: 245000, unit: '1 kg', stock: 42, organic: true, verified: true, category: 'Nuts', rating: 4.8 },
  { id: 'p002', name: 'Saffron Threads', producer: 'Khorasan Organic Farm', price: 8900000, unit: '5 g', stock: 8, organic: true, verified: true, category: 'Spices', rating: 4.9 },
  { id: 'p003', name: 'Organic Walnuts', producer: 'Gilan Mountain Co-op', price: 1850000, unit: '500 g', stock: 15, organic: true, verified: false, category: 'Nuts', rating: 4.6 },
  { id: 'p004', name: 'Wild Thyme Honey', producer: 'Kerman Beekeepers', price: 3200000, unit: '500 g', stock: 25, organic: true, verified: true, category: 'Honey', rating: 4.7 },
  { id: 'p005', name: 'Pomegranate Molasses', producer: 'Kashan Fruit Processors', price: 480000, unit: '500 ml', stock: 0, organic: false, verified: false, category: 'Condiments', rating: 4.2 },
  { id: 'p006', name: 'Dried Figs', producer: 'Fars Valley Farms', price: 650000, unit: '1 kg', stock: 33, organic: true, verified: true, category: 'Dried Fruit', rating: 4.5 },
];

export default function BazaarPage({ params }: { params: Promise<{ id: string }> }) {
  const t = useTranslations('market.bazaars');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';
  const [bazaarId] = useState('b001');

  const bazaar = MOCK_BAZAAR;
  const [products, setProducts] = useState<BazaarProduct[]>(MOCK_PRODUCTS);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'price-low' | 'price-high' | 'rating'>('rating');

  const categories = ['all', ...Array.from(new Set(products.map(p => p.category)))];

  const filtered = products
    .filter(p => categoryFilter === 'all' || p.category === categoryFilter)
    .sort((a, b) => {
      switch (sortBy) {
        case 'price-low': return a.price - b.price;
        case 'price-high': return b.price - a.price;
        default: return b.rating - a.rating;
      }
    });

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const handleProductClick = (id: string) => {
    router.push(`/${locale}/market/product/${id}`);
  };

  const handleBack = () => {
    router.push(`/${locale}/market/bazaars`);
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <button
              onClick={handleBack}
              className="text-sm text-ink-soft hover:text-ink underline"
            >
              {common('back')}
            </button>
          </nav>
          <div className="flex items-center justify-between">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{bazaar.name}</h1>
            <ProvenanceStamp
              source={bazaar.signature}
              verified={true}
              label={t('institutionalBazaar')}
            />
          </div>
        </header>

        <Card density="compact" className="mb-8">
          <p className="text-ink-soft mb-4">{bazaar.description}</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <span className="text-xs text-ink-soft">{t('location')}</span>
              <p className="font-medium text-ink">{bazaar.location}</p>
            </div>
            <div>
              <span className="text-xs text-ink-soft">{t('stores')}</span>
              <p className="font-medium text-ink">{bazaar.members} {common('stores')}</p>
            </div>
            <div>
              <span className="text-xs text-ink-soft">{t('established')}</span>
              <p className="font-medium text-ink">{bazaar.established}</p>
            </div>
            <div>
              <span className="text-xs text-ink-soft">{t('signature')}</span>
              <p className="font-medium text-ink font-mono">{bazaar.signature}</p>
            </div>
          </div>
        </Card>

        <Card density="compact" className="mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`px-4 py-2 rounded-md text-sm font-medium ${
                    categoryFilter === cat
                      ? 'bg-forest text-paper'
                      : 'bg-surface-alt text-ink-soft hover:text-ink'
                  }`}
                >
                  {cat === 'all' ? common('all') : cat}
                </button>
              ))}
            </div>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as typeof sortBy)}
              className="px-3 py-2 rounded border border-line bg-surface text-ink text-sm focus:outline-none focus:ring-2 focus:ring-forest"
            >
              <option value="rating">{common('sortByRating')}</option>
              <option value="price-low">{common('sortByPriceLow')}</option>
              <option value="price-high">{common('sortByPriceHigh')}</option>
            </select>
          </div>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map(product => (
            <Card key={product.id} density="compact">
              <div onClick={() => handleProductClick(product.id)} className="cursor-pointer">
                <div className="flex h-20 w-full items-center justify-center rounded border border-line bg-surface">
                  📷
                </div>
                <h3 className="font-medium text-ink mt-2">{product.name}</h3>
                <p className="text-sm text-ink-soft">{product.producer}</p>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <div>
                  <p className="text-ink-soft text-xs">{product.unit}</p>
                  <p className="font-bold text-forest">{formatPrice(product.price)} ریال</p>
                </div>
                <StatusDot
                  state={product.stock > 0 ? 'ok' : 'down'}
                  label={product.stock > 0 ? common('inStock') : common('outOfStock')}
                />
              </div>
              {product.organic && (
                <span className="mt-2 text-xs bg-forest/10 text-forest px-2 py-1 rounded">
                  {common('organic')}
                </span>
              )}
            </Card>
          ))}
        </div>

        {filtered.length === 0 && (
          <Card density="cozy" className="text-center py-8">
            <p className="text-ink-soft">{common('noResults')}</p>
          </Card>
        )}
      </div>
    </main>
  );
}
