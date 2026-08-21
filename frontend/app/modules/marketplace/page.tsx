"use client";
import { useState, useEffect } from 'react';
import Footer from '../../../components/layout/Footer';
import ProductCard from '../../../components/marketplace/ProductCard';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { api } from '../../../lib/api-client';
import { motion } from 'framer-motion';
import { ShoppingCart, Search, Filter } from 'lucide-react';

const CATEGORIES = ['all', 'grain', 'spice', 'nut', 'fruit', 'vegetable', 'herb', 'honey'];

export default function MarketplacePage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const [products, setProducts] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadProducts(); }, []);

  const loadProducts = async () => {
    setLoading(true);
    const res = await api.get<any>('/api/v1/marketplace/products');
    if (res.success && res.data) {
      const items = res.data.products || res.data || [];
      // Add sample data if empty
      if (items.length === 0) {
        setProducts([
          { id: 1, name: 'Organic Wheat', description: 'Premium quality organic wheat from sustainable farms', category: 'grain', price: 15.50, quantity: 500, is_organic: true, producer_name: 'Green Valley Farm' },
          { id: 2, name: 'Saffron Premium', description: 'Hand-picked Persian saffron, highest grade', category: 'spice', price: 450.00, quantity: 50, is_organic: true, producer_name: 'Red Gold Co.' },
          { id: 3, name: 'Roasted Pistachios', description: 'Salted and roasted, natural flavor', category: 'nut', price: 28.00, quantity: 200, is_organic: true, producer_name: 'Nut Valley' },
          { id: 4, name: 'Fresh Apples', description: 'Crispy organic apples, locally grown', category: 'fruit', price: 3.50, quantity: 1000, is_organic: true, producer_name: 'Orchard Hills' },
          { id: 5, name: 'Mountain Honey', description: 'Pure wildflower honey from highlands', category: 'honey', price: 18.00, quantity: 80, is_organic: true, producer_name: 'Bee Garden' },
          { id: 6, name: 'Fresh Spinach', description: 'Hydroponic fresh spinach leaves', category: 'vegetable', price: 4.20, quantity: 300, is_organic: false, producer_name: 'Urban Greens' },
          { id: 7, name: 'Dried Mint', description: 'Aromatic dried mint for tea and cooking', category: 'herb', price: 8.50, quantity: 150, is_organic: true, producer_name: 'Herb Garden' },
          { id: 8, name: 'Walnuts', description: 'Raw organic walnuts, brain-shaped health', category: 'nut', price: 22.00, quantity: 120, is_organic: true, producer_name: 'Nut Valley' },
        ]);
      } else {
        setProducts(items);
      }
    }
    setLoading(false);
  };

  const filtered = products.filter(p => {
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) ||
                       (p.description || '').toLowerCase().includes(search.toLowerCase());
    const matchCategory = category === 'all' || p.category === category;
    return matchSearch && matchCategory;
  });

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 20px' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, ${colors.primary}, #fb7185)`,
            padding: '32px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <ShoppingCart size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>{t('module_marketplace')}</h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                Sustainable products from verified local farmers
              </p>
            </div>
          </div>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: colors.cardBg, padding: '20px', borderRadius: '16px',
            border: `1px solid ${colors.border}`, marginBottom: '24px',
          }}
        >
          <div style={{ display: 'flex', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
              <Search size={16} color={colors.textMuted}
                style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                value={search} onChange={(e) => setSearch(e.target.value)}
                aria-label={t('marketplace_search')} placeholder={t('marketplace_search')}
                style={{
                  width: '100%', padding: '10px 12px 10px 38px', borderRadius: '10px',
                  border: `1px solid ${colors.border}`, background: colors.bg,
                  color: colors.text, fontFamily: 'inherit', fontSize: '0.9rem',
                }}
              />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {CATEGORIES.map(cat => (
              <motion.button
                key={cat}
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={() => setCategory(cat)}
                style={{
                  padding: '6px 14px', borderRadius: '100px',
                  background: category === cat
                    ? `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`
                    : colors.bg,
                  color: category === cat ? 'white' : colors.text,
                  border: category === cat ? 'none' : `1px solid ${colors.border}`,
                  cursor: 'pointer', fontSize: '0.85rem', fontWeight: '500',
                  textTransform: 'capitalize', fontFamily: 'inherit',
                }}
              >
                {cat}
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Products */}
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: colors.textMuted }}>
            Loading marketplace...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: colors.textMuted }}>
            No products found
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(270px, 1fr))', gap: '20px' }}>
            {filtered.map((p, i) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
