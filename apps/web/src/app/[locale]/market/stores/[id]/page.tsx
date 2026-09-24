'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';

interface SellerProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  unit: string;
  stock: number;
  organic: boolean;
  verified: boolean;
  category: string;
  rating: number;
  image?: string;
}

interface SellerInfo {
  id: string;
  name: string;
  producer: string;
  description: string;
  location: string;
  memberSince: string;
  verification: string;
  totalSales: number;
  rating: number;
  specialties: string[];
}

const MOCK_SELLER: SellerInfo = {
  id: 's001',
  name: 'Kerman Organic Cooperative',
  producer: 'کشاورزان ارگانیک کرمان',
  description:
    'Founded in 2023, we are a collective of 24 organic pistachio farmers committed to regenerative agriculture and fair trade.',
  location: 'Kerman Province, Iran',
  memberSince: '2023-03-15',
  verification: 'Certified Organic + Carbon Negative',
  totalSales: 342,
  rating: 4.85,
  specialties: ['Pistachios', 'Walnuts', 'Dried Fruits'],
};

const MOCK_PRODUCTS: SellerProduct[] = [
  {
    id: 'p001',
    name: 'Premium Pistachio Kernels',
    description: 'Hand-selected, roasted without salt, cold-pressed.',
    price: 245000,
    unit: '1 kg',
    stock: 42,
    organic: true,
    verified: true,
    category: 'Nuts & Seeds',
    rating: 4.9,
  },
  {
    id: 'p002',
    name: 'Shelled Pistachios',
    description: 'Raw, unsalted, ready to eat.',
    price: 198000,
    unit: '500 g',
    stock: 25,
    organic: true,
    verified: true,
    category: 'Nuts & Seeds',
    rating: 4.7,
  },
  {
    id: 'p003',
    name: 'Pistachio Kernels (Bulk)',
    description: 'Economy pack for commercial use.',
    price: 5750000,
    unit: '25 kg',
    stock: 5,
    organic: true,
    verified: false,
    category: 'Nuts & Seeds',
    rating: 4.5,
  },
  {
    id: 'p004',
    name: 'Pistachio Oil',
    description: 'Cold-pressed oil from pistachio kernels.',
    price: 1250000,
    unit: '250 ml',
    stock: 12,
    organic: true,
    verified: true,
    category: 'Oils',
    rating: 4.6,
  },
];

export default function StorePage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const t = useTranslations('market.stores');
  const common = useTranslations('common');
  const { locale, id: storeId } = useParamsSafe(params);
  const router = useRouter();

  const seller = MOCK_SELLER;
  const [products] = useState<SellerProduct[]>(MOCK_PRODUCTS);
  const [categoryFilter, setCategoryFilter] = useState('all');

  const categories = ['all', ...Array.from(new Set(products.map(p => p.category)))];

  const filtered = products.filter(p => categoryFilter === 'all' || p.category === categoryFilter);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const handleProductClick = (id: string) => {
    router.push(`/${locale}/market/product/${id}`);
  };

  const handleBack = () => {
    router.push(`/${locale}/market`);
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
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{seller.name}</h1>
              <p className="mt-1 text-ink-soft">{seller.location}</p>
            </div>
            <div className="flex items-center gap-4">
              <StatusDot
                state={seller.rating >= 4.5 ? 'ok' : seller.rating >= 3 ? 'warn' : 'down'}
                label={`⭐ ${seller.rating}`}
              />
              <ProvenanceStamp
                source={seller.verification}
                verified={true}
                label={t('verifiedSeller')}
              />
            </div>
          </div>
          <p className="text-ink-soft">{seller.description}</p>
        </header>

        <Card density="compact" className="mb-8">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <span className="text-xs text-ink-soft">{t('memberSince')}</span>
              <p className="font-medium text-ink">{seller.memberSince}</p>
            </div>
            <div>
              <span className="text-xs text-ink-soft">{t('totalSales')}</span>
              <p className="font-medium text-ink">{seller.totalSales} {common('orders')}</p>
            </div>
            <div>
              <span className="text-xs text-ink-soft">{t('rating')}</span>
              <p className="font-medium text-ink">⭐ {seller.rating}</p>
            </div>
            <div>
              <span className="text-xs text-ink-soft">{t('verification')}</span>
              <p className="font-medium text-ink">{seller.verification}</p>
            </div>
          </div>

          {seller.specialties.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-ink-soft mb-2">{t('specialties')}</p>
              <div className="flex flex-wrap gap-2">
                {seller.specialties.map(spec => (
                  <span key={spec} className="text-xs px-2 py-1 rounded bg-forest/10 text-forest">
                    {spec}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>

        <Card density="compact" className="mb-6">
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
        </Card>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map(product => (
            <Card key={product.id} density="compact">
              <div onClick={() => handleProductClick(product.id)} className="cursor-pointer">
                <div className="flex h-24 w-full items-center justify-center rounded border border-line bg-surface">
                  📷
                </div>
                <h3 className="font-medium text-ink mt-3">{product.name}</h3>
                <p className="text-sm text-ink-soft mt-1 line-clamp-2">{product.description}</p>
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
              {product.verified && (
              <div className="mt-2">
                <ProvenanceStamp
                  source="Verified Supplier"
                  verified={true}
                  label={common('verified')}
                />
              </div>
              )}
            </Card>
          ))}
        </div>

        {filtered.length === 0 && (
          <Card density="cozy" className="text-center py-8">
            <p className="text-ink-soft">{common('noResults')}</p>
          </Card>
        )}

        <Card density="compact" className="mt-8">
          <ProvenanceStamp
            source="Seller Profile"
            verified={true}
            method="Cooperative registry"
            label={t('storeProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}

function useParamsSafe(params: Promise<{ locale: string; id: string }>) {
  const [resolved, setResolved] = useState<{ locale: string; id: string } | null>(null);
  if (typeof window === 'undefined') {
    if (!resolved) {
      params.then(setResolved);
    }
    return { locale: '', id: '' };
  }
  return resolved || { locale: '', id: '' };
}
