export { default as fa } from './locales/fa';
export { default as en } from './locales/en';
export { DirectionProvider } from './DirectionProvider';
export { setupI18n } from './config';

// hooks (added by fix_hooks_export) — the official i18next API
export { useLocale, useSwitchLocale, useIsRtl, useDocumentDirection } from './hooks';
