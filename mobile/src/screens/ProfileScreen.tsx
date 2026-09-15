/** Profile screen for React Native. */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useBilingual } from '../hooks/useBilingual';

export default function ProfileScreen() {
  const { fa, lang } = useBilingual();
  const isFa = lang === 'fa';

  const settings = [
    { icon: 'person', title: isFa ? 'پروفایل' : 'Profile' },
    { icon: 'notifications', title: isFa ? 'اعلانات' : 'Notifications' },
    { icon: 'key', title: isFa ? 'امنیت' : 'Security' },
    { icon: 'globe', title: isFa ? 'زبان' : 'Language' },
    { icon: 'moon', title: isFa ? 'حالت تاریک' : 'Dark Mode' },
    { icon: 'log-out', title: isFa ? 'خروج' : 'Logout' },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>👤</Text>
        </View>
        <Text style={styles.name}>Eco Nojin</Text>
        <Text style={styles.email}>farmer@ecnojin.ir</Text>
      </View>
      {settings.map((item) => (
        <TouchableOpacity key={item.icon} style={styles.setting}>
          <Ionicons name={item.icon as any} size={22} color="#86868b" />
          <Text style={styles.settingTitle}>{item.title}</Text>
          <Ionicons name="chevron-forward" size={20} color="#c7c7cc" />
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f7' },
  header: { alignItems: 'center', paddingVertical: 32 },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#e5e5ea', alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 32 },
  name: { fontSize: 18, fontWeight: '700', color: '#1d1d1f', marginTop: 12 },
  email: { fontSize: 13, color: '#86868b', marginTop: 2 },
  setting: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#ffffff', padding: 16, marginHorizontal: 20, marginBottom: 1, borderRadius: 12 },
  settingTitle: { flex: 1, fontSize: 15, color: '#1d1d1f', marginLeft: 12 },
});
