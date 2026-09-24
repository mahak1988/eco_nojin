'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';

interface Product {
  id: string;
  name: string;
  producer: string;
  price: number;
  unit: string;
  category: string;
  origin: string;
  stock: number;
  rating: number;
  impact: { carbon: number; water: number; soil: number };
  organic: boolean;
  verified: boolean;
}

const MOCK_PRODUCTS: Product[] = [
  {
    id: 'p001',
    name: 'Organic Pistachio Kernels',
    producer: 'Kerman Cooperative',
    price: 245000,
    unit: '1 kg',
    category: 'Nuts & Seeds',
    origin: 'Kerman Province',
    stock: 42,
    rating: 4.8,
    impact: { carbon: 12.4, water: 850, soil: 3.2 },
    organic: true,
    verified: true,
  },
  {
    id: 'p002',
    name: 'Saffron Threads',
    producer: 'Khorasan Organic Farm',
    price: 8900000,
    unit: '5 g',
    category: 'Spices',
    origin: 'Khorasan Province',
    stock: 8,
    rating: 4.9,
    impact: { carbon: 2.1, water: 1200, soil: 4.5 },
    organic: true,
    verified: true,
  },
  {
    id: 'p003',
    name: 'Organic Walnuts',
    producer: 'Gilan Mountain Co-op',
    price: 1850000,
    unit: '500 g',
    category: 'Nuts & Seeds',
    origin: 'Gilan Province',
    stock: 15,
    rating: 4.6,
    impact: { carbon: 8.7, water: 650, soil: 5.1 },
    organic: true,
    verified: false,
  },
  {
    id: 'p004',
    name: 'Dried Apricots',
    producer: 'Kerman Fruit Co.',
    price: 980000,
    unit: '1 kg',
    category: 'Dried Fruit',
    origin: 'Kerman Province',
    stock: 0,
    rating: 4.3,
    impact: { carbon: 5.2, water: 750, soil: 2.8 },
    organic: false,
    verified: false,
  },
];

export default function ComparePage() {
  const t = useTranslations('market.compare');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const [selected, setSelected] = useState<string[]>(['p001', 'p002']);

  const selectedProducts = MOCK_PRODUCTS.filter(p => selected.includes(p.id)).slice(0, 4);

  const toggleProduct = (id: string) => {
    if (selected.includes(id)) {
      setSelected(selected.filter(s => s !== id));
    } else if (selected.length < 4) {
      setSelected([...selected, id]);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const fields = [
    { key: 'price', label: t('price'), render: (p: Product) => `${formatPrice(p.price)} ریال / ${p.unit}` },
    { key: 'category', label: t('category'), render: (p: Product) => p.category },
    { key: 'origin', label: t('origin'), render: (p: Product) => p.origin },
    { key: 'producer', label: t('producer'), render: (p: Product) => p.producer },
    { key: 'rating', label: t('rating'), render: (p: Product) => `⭐ ${p.rating}` },
    { key: 'stock', label: t('availability'), render: (p: Product) => p.stock > 0 ? t('inStock') : t('outOfStock') },
    { key: 'organic', label: t('organic'), render: (p: Product) => (p.organic ? t('yes') : t('no')) },
    { key: 'verified', label: t('verified'), render: (p: Product) => (p.verified ? t('yes') : t('no')) },
    { key: 'carbon', label: t('carbonImpact'), render: (p: Product) => `${p.impact.carbon} kg CO₂` },
    { key: 'water', label: t('waterImpact'), render: (p: Product) => `${p.impact.water} L` },
    { key: 'soil', label: t('soilImpact'), render: (p: Product) => `${p.impact.soil} t/ha` },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-6xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-2 text-ink-soft">{t('lead')}</p>
        </header>

        <Card density="compact" className="mb-8">
          <h2 className="font-medium text-ink mb-4">{t('selectProducts')}</h2>
          <p className="text-sm text-ink-soft mb-3">
            {t('maxFour')}: {selected.length}/4
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {MOCK_PRODUCTS.map(product => (
              <button
                key={product.id}
                onClick={() => toggleProduct(product.id)}
                disabled={!selected.includes(product.id) && selected.length >= 4}
                className={`p-3 rounded-md border text-left ${
                  selected.includes(product.id)
                    ? 'border-forest bg-forest/5'
                    : 'border-line hover:border-ink/30'
                }`}
              >
                <p className="font-medium text-ink">{product.name}</p>
                <p className="text-sm text-ink-soft">{product.producer}</p>
              </button>
            ))}
          </div>
        </Card>

        {selectedProducts.length > 0 && (
          <Card density="compact">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className="text-left py-3 px-3 font-medium text-ink-soft">{t('feature')}</th>
                    {selectedProducts.map(p => (
                      <th key={p.id} className="text-center py-3 px-3">
                        <p className="font-medium text-ink">{p.name}</p>
                        <p className="text-xs text-ink-soft">{p.producer}</p>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fields.map(field => (
                    <tr key={field.key} className="border-b border-line/50">
                      <td className="py-3 px-3 font-medium text-ink">{field.label}</td>
                      {selectedProducts.map(p => (
                        <td key={p.id} className="py-3 px-3 text-center">
                          {field.render(p)}
                        </td>
                      ))}
                    </tr>
                  ))}
                  <tr className="border-b border-line/50">
                    <td className="py-3 px-3 font-medium text-ink">{t('actions')}</td>
                    {selectedProducts.map(p => (
                      <td key={p.id} className="py-3 px-3 text-center">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => router.push(`/${locale}/market/product/${p.id}`)}
                        >
                          {common('view')}
                        </Button>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-4 text-center">
              <p className="text-xs text-ink-soft">
                {t('antiFraudWarning')}
              </p>
            </div>
          </Card>
        )}

        {selectedProducts.length === 0 && (
          <Card density="cozy" className="text-center py-8">
            <p className="text-ink-soft">{t('noProductsSelected')}</p>
          </Card>
        )}

        <Card density="compact" className="mt-8">
          <ProvenanceStamp
            source="Compare Service"
            verified={true}
            method="Price API"
            label={t('compareProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}
