"use client";
import { useEffect, ReactNode } from 'react';

export function FontLanguageProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    
    const getLanguage = (): string => {
      if (typeof window === 'undefined') return 'fa';
      return localStorage.getItem('locale') || 'fa';
    };
    
    const applyFont = () => {
      const language = getLanguage();
      const rtlLangs = ['fa', 'ar', 'ur', 'he', 'ps'];
      const isRtl = rtlLangs.includes(language);
      html.setAttribute('dir', isRtl ? 'rtl' : 'ltr');
      html.setAttribute('lang', language);
      body.classList.remove('lang-fa', 'lang-en', 'lang-ar', 'lang-tr', 'lang-ur', 'lang-he');
      body.classList.add('lang-' + language);
    };
    
    applyFont();
    
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'locale') applyFont();
    };
    const handleLocaleChange = () => applyFont();
    window.addEventListener('storage', handleStorage);
    window.addEventListener('locale-change', handleLocaleChange);
    
    // No polling: font/dir updates are event-driven (locale-change + cross-tab storage).
    
    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('locale-change', handleLocaleChange);
    };
  }, []);
  
  return <>{children}</>;
}
