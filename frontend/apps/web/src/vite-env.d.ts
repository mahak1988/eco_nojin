/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_MAP_STYLE_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_SUPABASE_URL?: string;
  readonly VITE_SUPABASE_ANON_KEY?: string;
  readonly VITE_DEFAULT_LOCALE?: 'en' | 'fa' | 'ar' | 'ur';
  readonly VITE_FF_NEW_LAYOUT?: string;
  readonly VITE_FF_REALTIME?: string;
  readonly VITE_FF_AI?: string;
  readonly VITE_FF_CARBON?: string;
  readonly VITE_FF_MARKETPLACE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}