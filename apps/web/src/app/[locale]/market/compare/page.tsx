'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { searchProducts } from '@/lib/api/market';
import type { ProductListing } from '@/types/market';

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
}

const PRODUCTS_SOURCE = '/api/v1/marketplace/products';

function mapProduct(item: ProductListing, locale: string): Product {
  return {
    id: item.id,
    name: item.name[locale] ?? item.name.en ?? item.id,
    producer: item.producer.name,
    price: item.price,
    unit: item.unit,
    category: item.category.name[locale] ?? item.category.name.en ?? item.category.slug,
    origin: item.origin ?? item.location?.address ?? '',
    stock: item.stockQuantity ?? 0,
    rating: item.producer.rating ?? 0,
    impact: { carbon: item.carbonFootprint ?? 0, water: item.waterFootprint ?? 0, soil: 0 },
    organic: item.organic,
  };
}

export default function ComparePage() {
  const t = useTranslations('market.compare');
  const common = useTranslations('common');
  const pathname = usePathname();
  const router = useRouter();
  const locale = pathname.split('/')[1] || 'fa';

  const [products, setProducts] = useState<Product[]>([]);
  const [dataState, setDataState] = useState<'loading' | 'live' | 'unavailable'>('loading');
  const [selected, setSelected] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    void searchProducts({}).then((result) => {
      if (!active) return;
      if (result.ok && result.data.products.length > 0) {
        setProducts(result.data.products.map((item) => mapProduct(item, locale)));
        setDataState('live');
      } else {
        setDataState('unavailable');
      }
    });
    return () => {
      active = false;
    };
  }, [locale]);

  const selectedProducts = products.filter((p) => selected.includes(p.id)).slice(0, 4);

  const toggleProduct = (id: string) => {
    if (selected.includes(id)) {
      setSelected(selected.filter((s) => s !== id));
    } else if (selected.length < 4) {
      setSelected([...selected, id]);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-US').format(price);
  };

  const fields = [
    {
      key: 'price',
      label: t('price'),
      render: (p: Product) => `${formatPrice(p.price)} ریال / ${p.unit}`,
    },
    { key: 'category', label: t('category'), render: (p: Product) => p.category },
    { key: 'origin', label: t('origin'), render: (p: Product) => p.origin },
    { key: 'producer', label: t('producer'), render: (p: Product) => p.producer },
    { key: 'rating', label: t('rating'), render: (p: Product) => `⭐ ${p.rating}` },
    {
      key: 'stock',
      label: t('availability'),
      render: (p: Product) => (p.stock > 0 ? t('inStock') : t('outOfStock')),
    },
    {
      key: 'organic',
      label: t('organic'),
      render: (p: Product) => (p.organic ? t('yes') : t('no')),
    },
    {
      key: 'carbon',
      label: t('carbonImpact'),
      render: (p: Product) => `${p.impact.carbon} kg CO₂`,
    },
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

        {dataState === 'unavailable' && (
          <p
            role="status"
            className="mb-6 rounded-md border border-line bg-surface-alt p-3 text-sm text-ink-soft"
          >
            {t('dataUnavailable')}
          </p>
        )}

        <Card density="compact" className="mb-8">
          <h2 className="font-medium text-ink mb-4">{t('selectProducts')}</h2>
          <p className="text-sm text-ink-soft mb-3">
            {t('maxFour')}: {selected.length}/4
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {products.map((product) => (
              <button
                type="button"
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
                    <th className="text-left py-3 px-3 font-medium text-ink-soft">
                      {t('feature')}
                    </th>
                    {selectedProducts.map((p) => (
                      <th key={p.id} className="text-center py-3 px-3">
                        <p className="font-medium text-ink">{p.name}</p>
                        <p className="text-xs text-ink-soft">{p.producer}</p>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fields.map((field) => (
                    <tr key={field.key} className="border-b border-line/50">
                      <td className="py-3 px-3 font-medium text-ink">{field.label}</td>
                      {selectedProducts.map((p) => (
                        <td key={p.id} className="py-3 px-3 text-center">
                          {field.render(p)}
                        </td>
                      ))}
                    </tr>
                  ))}
                  <tr className="border-b border-line/50">
                    <td className="py-3 px-3 font-medium text-ink">{t('actions')}</td>
                    {selectedProducts.map((p) => (
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
              <p className="text-xs text-ink-soft">{t('antiFraudWarning')}</p>
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
            source={PRODUCTS_SOURCE}
            verified={false}
            label={t('compareProvenance')}
          />
        </Card>
      </div>
    </main>
  );
}
