"use client";
import { motion } from 'framer-motion';
import { ShoppingCart, Leaf, Star, Package } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';

interface Product {
  id: number;
  name: string;
  description?: string;
  category: string;
  price: number;
  quantity: number;
  is_organic: boolean;
  producer_name?: string;
}

interface Props {
  product: Product;
  onBuy?: (p: Product) => void;
}

const CATEGORY_ICONS: Record<string, string> = {
  grain: 'ًںŒ¾', spice: 'ًںŒ¶ï¸ڈ', nut: 'ًں¥œ', fruit: 'ًںچژ',
  vegetable: 'ًں¥¬', herb: 'ًںŒ؟', dairy: 'ًں¥›', honey: 'ًںچ¯',
};

export default function ProductCard({ product, onBuy }: Props) {
  const { colors } = useTheme();

  return (
    <motion.div
      whileHover={{ y: -6, boxShadow: `0 20px 40px ${colors.primary}25` }}
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      style={{
        background: colors.cardBg, borderRadius: '20px',
        border: `1px solid ${colors.border}`, overflow: 'hidden',
        backdropFilter: 'blur(20px)', display: 'flex', flexDirection: 'column',
      }}
    >
      {/* Image placeholder */}
      <div style={{
        height: '160px',
        background: `linear-gradient(135deg, ${colors.primary}20, ${colors.accent}20)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative',
      }}>
        <div style={{ fontSize: '4rem' }}>
          {CATEGORY_ICONS[product.category] || 'ًں“¦'}
        </div>
        {product.is_organic && (
          <div style={{
            position: 'absolute', top: '10px', right: '10px',
            background: colors.success, color: 'white',
            padding: '4px 10px', borderRadius: '100px',
            fontSize: '0.7rem', fontWeight: '700',
            display: 'flex', alignItems: 'center', gap: '4px',
          }}>
            <Leaf size={12} /> Organic
          </div>
        )}
        {product.quantity < 10 && product.quantity > 0 && (
          <div style={{
            position: 'absolute', top: '10px', left: '10px',
            background: colors.warm, color: 'white',
            padding: '4px 10px', borderRadius: '100px',
            fontSize: '0.7rem', fontWeight: '700',
          }}>
            Low stock
          </div>
        )}
      </div>

      {/* Content */}
      <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{
          display: 'inline-block', padding: '2px 10px', borderRadius: '100px',
          background: `${colors.accent}15`, color: colors.accent,
          fontSize: '0.7rem', fontWeight: '600', textTransform: 'capitalize',
          marginBottom: '8px', alignSelf: 'flex-start',
        }}>
          {product.category}
        </div>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: colors.text, margin: '0 0 6px' }}>
          {product.name}
        </h3>
        {product.description && (
          <p style={{ fontSize: '0.85rem', color: colors.textMuted, margin: '0 0 12px', flex: 1 }}>
            {product.description}
          </p>
        )}
        {product.producer_name && (
          <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginBottom: '8px' }}>
            By: <span style={{ color: colors.text }}>{product.producer_name}</span>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: '800', color: colors.primary }}>
              ${product.price.toFixed(2)}
            </div>
            <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>
              Stock: {product.quantity}
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={() => onBuy?.(product)}
            disabled={product.quantity === 0}
            style={{
              padding: '10px 16px', borderRadius: '10px',
              background: product.quantity === 0 ? colors.textMuted
                : `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
              color: 'white', border: 'none', cursor: product.quantity === 0 ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: '6px',
              fontSize: '0.85rem', fontWeight: '600',
              boxShadow: product.quantity === 0 ? 'none' : `0 4px 12px ${colors.primary}40`,
            }}
          >
            <ShoppingCart size={14} />
            {product.quantity === 0 ? 'Out' : 'Buy'}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
