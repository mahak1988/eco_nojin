/** React Native hooks for bilingual content. */

import { useState, useMemo, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { I18nManager } from 'react-native';

const STORAGE_KEY = 'eco_nojin_lang';
const SUPPORTED_LANGS = ['fa', 'en', 'ur', 'ps'] as const;
export type Lang = (typeof SUPPORTED_LANGS)[number];

const CONTENT: Record<Lang, Record<string, string>> = {
  fa: {
    welcome: 'سلام 👋',
    subtitle: 'داشبورد کشاورزی هوشمند',
    models: 'مدل‌ها',
    satellite: 'ماهواره',
    mrv: 'MRV',
    indices: 'اندیکاتورها',
    water: 'آب',
    climate: 'آب‌وهوا',
    simulation: 'شبیه‌سازی',
    economy: 'اقتصاد',
    advisory: 'مشاوره',
    marketplace: 'بازارچه',
    loading: 'در حال بارگذاری...',
    error: 'خطا رخ داد',
  },
  en: {
    welcome: 'Welcome 👋',
    subtitle: 'Smart Farming Dashboard',
    models: 'Models',
    satellite: 'Satellite',
    mrv: 'MRV',
    indices: 'Indices',
    water: 'Water',
    climate: 'Climate',
    simulation: 'Simulation',
    economy: 'Economy',
    advisory: 'Advisory',
    marketplace: 'Marketplace',
    loading: 'Loading...',
    error: 'Error',
  },
  ur: {
    welcome: 'خوش آمدید 👋',
    subtitle: 'ہوشمند کسان ڈیشبورڈ',
    models: 'ماڈلز',
    satellite: 'سیٹلائیٹ',
    mrv: 'ایم آر وی',
    indices: 'اشاریے',
    water: 'پانی',
    climate: 'آب و ہوا',
    simulation: 'سمیشن',
    economy: 'معیشت',
    advisory: ' مشورہ',
    marketplace: 'مارکیٹ پلیس',
    loading: 'لوڈ ہو رہا ہے...',
    error: 'غلطی',
  },
  ps: {
    welcome: 'ښایي ته 👋',
    subtitle: 'هوښتیا د کسان ډیشبورډ',
    models: 'مدلونه',
    satellite: 'ماهواره',
    mrv: 'ایم آر وی',
    indices: 'شاخصونه',
    water: 'ښکته',
    climate: 'آب او هوا',
    simulation: 'شبیه‌سازی',
    economy: 'اقتصاد',
    advisory: 'مشوره',
    marketplace: 'بازارچه',
    loading: 'په لودونه کې...',
    error: 'غلطه',
  },
};

export function useBilingual() {
  const [lang, setLang] = useState<Lang>('fa');

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((stored) => {
      if (stored && SUPPORTED_LANGS.includes(stored as Lang)) {
        setLang(stored as Lang);
      }
    });
  }, []);

  const setLanguage = useCallback(async (newLang: Lang) => {
    if (!SUPPORTED_LANGS.includes(newLang)) return;
    await AsyncStorage.setItem(STORAGE_KEY, newLang);
    setLang(newLang);
    I18nManager.forceRTL(newLang === 'fa');
  }, []);

  const t = useMemo(() => CONTENT[lang], [lang]);
  const isFa = lang === 'fa';
  const isUr = lang === 'ur';
  const isPs = lang === 'ps';

  return { lang, setLang: setLanguage, t, isFa, isUr, isPs, getLocale: () => lang };
}
