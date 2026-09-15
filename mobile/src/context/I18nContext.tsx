/** React Native i18n context provider. */

import React, { createContext, useContext, type ReactNode } from 'react';
import { useBilingual, type Lang } from '../hooks/useBilingual';

interface I18nContextValue {
  lang: Lang;
  setLang: (lang: Lang) => Promise<void>;
  t: Record<string, string>;
  isFa: boolean;
  isUr: boolean;
  isPs: boolean;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const bilingual = useBilingual();

  return (
    <I18nContext.Provider
      value={{
        lang: bilingual.lang,
        setLang: bilingual.setLang,
        t: bilingual.t,
        isFa: bilingual.isFa,
        isUr: bilingual.isUr,
        isPs: bilingual.isPs,
      }}
    >
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n(): I18nContextValue {
  const value = useContext(I18nContext);
  if (!value) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return value;
}
