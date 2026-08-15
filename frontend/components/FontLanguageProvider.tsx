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
    window.addEventListener('storage', handleStorage);
    
    const interval = setInterval(applyFont, 500);
    
    return () => {
      window.removcEventListener('storage', handleStorage);
      clearInterval(interval);
    };
  }, []);
  
  return <>{children}</>;
}
