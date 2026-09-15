/** Marketplace screen for React Native. */

import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { useBilingual } from '../hooks/useBilingual';
import { listMarketplaceProducts, type Product } from '../services/api';

export default function MarketplaceScreen() {
  const { fa, lang } = useBilingual();
  const isFa = lang === 'fa';
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listMarketplaceProducts();
      setProducts(data.products as Product[]);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  const renderProduct = ({ item }: { item: Product }) => (
    <TouchableOpacity style={styles.product}>
      <Text style={styles.productName} numberOfLines={2}>{isFa ? (item as any).name_fa : (item as any).name_en}</Text>
      <Text style={styles.productPrice}>{(item as any).price_per_kg ?? 0} {isFa ? 'تومان/کیلو' : 'USD/kg'}</Text>
      <Text style={styles.productProducer}>{isFa ? 'فروشنده: ' : 'Seller: '}{(item as any).producer_name ?? 'Unknown'}</Text>
    </TouchableOpacity>
  );

  return (
    <FlatList
      style={styles.container}
      data={products}
      keyExtractor={(_, i) => String(i)}
      renderItem={renderProduct}
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={loadProducts} tintColor={isFa ? '#2d6a4f' : '#0071e3'} />}
      ListEmptyComponent={
        <View style={styles.empty}>
          <Text style={styles.emptyText}>{isFa ? 'در حال بارگذاری محصولات…' : 'Loading products…'}</Text>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f7' },
  list: { padding: 16, paddingBottom: 80 },
  product: { backgroundColor: '#ffffff', borderRadius: 12, padding: 16, marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1 },
  productName: { fontSize: 16, fontWeight: '700', color: '#1d1d1f', marginBottom: 4 },
  productPrice: { fontSize: 14, fontWeight: '600', color: '#0071e3', marginBottom: 4 },
  productProducer: { fontSize: 12, color: '#86868b' },
  empty: { alignItems: 'center', paddingTop: 60 },
  emptyText: { fontSize: 14, color: '#86868b' },
});
