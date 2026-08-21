"use client";
import { useEffect } from 'react';
import { useI18n } from './i18n-context';

/**
 * Hook to apply language-specific font classes to document
 * B Mitra: Persian (fa) - classic, formal text
 * Vazirmatn: Persian (fa), Arabic (ar) - modern UI
 * System fonts: English (en), Turkish (tr), etc
 */
export function useFontLanguage() {
  const { locale: language } = useI18n();
  
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    
    // Remove all lang-* classes
    body.classList.remove('lang-fa', 'lang-en', 'lang-ar', 'lang-tr');
    
    // Add current language class
    body.classList.add(`lang-${language}`);
    
    // Set direction
    const rtlLangs = ['fa', 'ar', 'ur', 'he', 'ps'];
    html.setAttribute('dir', rtlLangs.includes(language) ? 'rtl' : 'ltr');
    html.setAttribute('lang', language);
    
  }, [language]);
  
  return { language };
}

/**
 * Get appropriate font family for current language
 */
export function getFontFamily(language: string): string {
  switch (language) {
    case 'fa':
      return "var(--font-fa-classic)";
    case 'ar':
      return "var(--font-ar)";
    case 'en':
    case 'tr':
    default:
      return "var(--font-en)";
  }
}

/**
 * Check if language is RTL
 */
export function isRTL(language: string): boolean {
  return ['fa', 'ar', 'ur', 'he', 'ps'].includes(language);
}