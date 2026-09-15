/** Dashboard screen for React Native — main hub. */

import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useBilingual } from '../hooks/useBilingual';
import { apiFetch, getAuthHeaders } from '../services/api';
import { useFocusEffect } from '@react-navigation/native';

export default function DashboardScreen() {
  const { t, fa, lang } = useBilingual();
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<Record<string, number>>({ models: 0, devices: 0, projects: 0 });

  const isFa = lang === 'fa';

  const loadData = useCallback(async () => {
    setRefreshing(true);
    try {
      // Load dashboard data
    } catch {
      /* ignore */
    } finally {
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => {
    loadData();
  }, [loadData]));

  const quickActions = [
    { icon: 'leaf', title: isFa ? 'مدل‌ها' : 'Models', color: '#2d6a4f' },
    { icon: 'satellite', title: isFa ? 'ماهواره' : 'Satellite', color: '#1d3557' },
    { icon: 'cellular', title: isFa ? 'MRV' : 'MRV', color: '#457b9d' },
    { icon: 'flash', title: isFa ? 'اندیکاتورها' : 'Indices', color: '#e63946' },
    { icon: 'water', title: isFa ? 'آب' : 'Water', color: '#0077b6' },
    { icon: 'thermometer', title: isFa ? 'آب‌وهوا' : 'Climate', color: '#f4a261' },
    { icon: 'swap-horizontal', title: isFa ? 'شبیه‌سازی' : 'Simulation', color: '#2a9d8f' },
    { icon: 'coin', title: isFa ? 'اقتصاد' : 'Economy', color: '#e9c46a' },
  ];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={loadData} tintColor={isFa ? '#2d6a4f' : '#0071e3'} />}
    >
      <View style={styles.header}>
        <Text style={styles.greeting}>{isFa ? 'سلام 👋' : 'Welcome 👋'}</Text>
        <Text style={styles.subtitle}>{isFa ? 'داشبورد کشاورزی هوشمند' : 'Smart Farming Dashboard'}</Text>
      </View>

      <View style={styles.statsRow}>
        {Object.entries(stats).map(([key, value]) => (
          <View key={key} style={styles.statCard}>
            <Text style={styles.statValue}>{value}</Text>
            <Text style={styles.statLabel}>{isFa ? key : key}</Text>
          </View>
        ))}
      </View>

      <View style={styles.quickActionsHeader}>
        <Text style={styles.sectionTitle}>{isFa ? 'ابزارهای سریع' : 'Quick Tools'}</Text>
      </View>
      <View style={styles.quickActionsGrid}>
        {quickActions.map((action) => (
          <TouchableOpacity key={action.icon} style={styles.quickAction}>
            <Ionicons name={action.icon as any} size={24} color={action.color} />
            <Text style={styles.quickActionTitle} numberOfLines={2}>{action.title}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>{isFa ? 'مشاوره هوشمند' : 'AI Advisory'}</Text>
        <Text style={styles.cardText} numberOfLines={2}>
          {isFa ? 'پاسخ‌هایی مبتنی بر مستندات علمی و شاخص‌های ماهواره‌ای.' : 'Evidence-based recommendations with scientific references.'}
        </Text>
        <TouchableOpacity style={styles.cardButton} onPress={() => {}}>
          <Text style={styles.cardButtonText}>{isFa ? 'باز کردن' : 'Open'}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>{isFa ? 'وضعیت دستگاه‌ها' : 'Device Status'}</Text>
        <Text style={styles.cardText} numberOfLines={2}>
          {isFa ? 'بررسی دستگاه‌های IoT فعال' : 'Check active IoT devices'}
        </Text>
        <TouchableOpacity style={styles.cardButton} onPress={() => {}}>
          <Text style={styles.cardButtonText}>{isFa ? 'باز کردن' : 'Open'}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f7',
  },
  header: {
    padding: 20,
    paddingBottom: 12,
  },
  greeting: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1d1d1f',
  },
  subtitle: {
    fontSize: 14,
    color: '#86868b',
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 4,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1d1d1f',
  },
  statLabel: {
    fontSize: 12,
    color: '#86868b',
    marginTop: 4,
  },
  quickActionsHeader: {
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1d1d1f',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  quickAction: {
    width: '23%',
    aspectRatio: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    margin: '1%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  quickActionTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: '#1d1d1f',
    textAlign: 'center',
    marginTop: 8,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1d1d1f',
    marginBottom: 6,
  },
  cardText: {
    fontSize: 13,
    color: '#86868b',
    marginBottom: 12,
  },
  cardButton: {
    backgroundColor: '#0071e3',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignSelf: 'flex-start',
  },
  cardButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
});
