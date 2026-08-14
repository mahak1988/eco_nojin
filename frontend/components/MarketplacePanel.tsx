'use client';
import { useState, useEffect } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

interface Product {
  id: string;
  name: string;
  category: string;
  price_per_kg: number;
  quantity_available_kg: number;
  organic_certified: boolean;
  producer_name: string;
  origin_location: string;
  traceability_code: string;
}

export default function MarketplacePanel() {
  const { t } = useI18n();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [organicOnly, setOrganicOnly] = useState(false);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (categoryFilter) params.append('category', categoryFilter);
      if (organicOnly) params.append('organic_only', 'true');

      const res = await fetch(`${API_BASE}/api/v1/marketplace/products?${params}`);
      const data = await res.json();
      setProducts(data.products || []);
    } catch (err) {
      console.error('Failed to fetch products:', err);
    } finally {
      setLoading(false);
    }
  };

  const categoryColors: Record<string, string> = {
    grains: '#f59e0b',
    vegetables: '#22c55e',
    fruits: '#ef4444',
    herbs_medicinal: '#8b5cf6',
    dairy: '#3b82f6',
    honey: '#eab308',
    handicrafts: '#ec4899',
    seeds: '#14b8a6',
    fertilizer_organic: '#84cc16',
    other: '#6b7280',
  };

  return (
    <section
      aria-labelledby="marketplace-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#fff',
      }}
    >
      <h2 id="marketplace-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#0c4a6e' }}>
        🛒 {t('marketplace_title')}
      </h2>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder={t('search_products')}
          aria-label={t('search_products')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '6px', flex: 1, minWidth: '200px' }}
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          aria-label={t('all_categories')}
          style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
        >
          <option value="">{t('all_categories')}</option>
          {Object.keys(categoryColors).map(cat => (
            <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
          ))}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <input
            type="checkbox"
            checked={organicOnly}
            onChange={(e) => setOrganicOnly(e.target.checked)}
          />
          {t('organic_only')}
        </label>
        <button
          onClick={fetchProducts}
          aria-label={t('apply_filters')}
          style={{ padding: '8px 16px', background: '#0369a1', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          {t('apply_filters')}
        </button>
      </div>

      {/* Products Grid */}
      <div aria-live="polite">
        {loading ? (
          <p style={{ color: '#666' }}>{t('analyzing')}</p>
        ) : products.length === 0 ? (
          <p style={{ color: '#666' }}>{t('no_products')}</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {products.map((product) => (
              <div key={product.id} style={{
                padding: '16px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                background: '#f9fafb',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: '600', margin: 0 }}>{product.name}</h3>
                  {product.organic_certified && (
                    <span style={{ background: '#22c55e', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem' }}>
                      🌱 {t('organic_only')}
                    </span>
                  )}
                </div>

                <span style={{
                  display: 'inline-block',
                  padding: '2px 10px',
                  borderRadius: '12px',
                  fontSize: '0.75rem',
                  background: categoryColors[product.category] || '#6b7280',
                  color: 'white',
                  marginBottom: '8px',
                }}>
                  {product.category.replace('_', ' ')}
                </span>

                <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>
                  <p style={{ margin: '4px 0' }}><strong>{t('producer')}:</strong> {product.producer_name}</p>
                  <p style={{ margin: '4px 0' }}><strong>{t('origin')}:</strong> {product.origin_location}</p>
                  <p style={{ margin: '4px 0' }}><strong>{t('available')}:</strong> {product.quantity_available_kg.toLocaleString()} kg</p>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#0c4a6e' }}>
                    ${product.price_per_kg.toFixed(2)}/kg
                  </span>
                  <button
                    style={{ padding: '6px 16px', background: '#15803d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                    onClick={() => alert(`Order placed for ${product.name}!`)}
                  >
                    {t('order')}
                  </button>
                </div>

                <p style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '8px' }}>
                  {t('trace')}: {product.traceability_code}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
