/** Profile & settings page content (dashboard account pages, bilingual). */

export interface ProfileContent {
  kicker: string;
  title: string;
  lead: string;
  clientKeyTitle: string;
  clientKeyHint: string;
  copy: string;
  copied: string;
  displayNameTitle: string;
  displayNameLabel: string;
  displayNameHint: string;
  save: string;
  saved: string;
  runsTitle: string;
  privacyNote: string;
}

export interface SettingsContent {
  kicker: string;
  title: string;
  lead: string;
  apiTitle: string;
  apiHint: string;
  apiLabel: string;
  apiSave: string;
  apiSaved: string;
  apiInvalid: string;
  langTitle: string;
  langHint: string;
  dataTitle: string;
  dataHint: string;
  dataButton: string;
  dataDone: string;
  endpointsTitle: string;
  endpoints: { method: string; path: string; desc: string }[];
}

export const profileSettings = {
  fa: {
    profile: {
      kicker: 'حساب کاربری',
      title: 'پروفایل',
      lead: 'هویت شما در داشبورد هیدروما — محلی و بدون ارسال به سرور.',
      clientKeyTitle: 'کلید کاربر (ناشناس)',
      clientKeyHint: 'این کلید هویت شما در مرکز تجمیع است؛ اجراهای مدل‌ها با همین کلید ذخیره می‌شوند. آن را با کسی به اشتراک نگذارید.',
      copy: 'کپی',
      copied: 'کپی شد ✓',
      displayNameTitle: 'نام نمایشی',
      displayNameLabel: 'نام نمایشی شما',
      displayNameHint: 'فقط روی همین دستگاه ذخیره می‌شود.',
      save: 'ذخیره',
      saved: 'ذخیره شد ✓',
      runsTitle: 'اجراهای ثبت‌شده من',
      privacyNote: 'طبق سیاست حریم خصوصی: بدون IP، بدون ردیاب، بدون ارسال داده شخصی.',
    },
    settings: {
      kicker: 'تنظیمات',
      title: 'تنظیمات پلتفرم',
      lead: 'پیکربندی محلی داشبورد — آدرس درگاه، زبان و داده‌های محلی.',
      apiTitle: 'آدرس درگاه API',
      apiHint: 'پیش‌فرض: http://localhost:8000 — برای سرور دیگر آدرس را عوض کنید (بلافاصله اعمال می‌شود).',
      apiLabel: 'آدرس درگاه',
      apiSave: 'ذخیره آدرس',
      apiSaved: 'ذخیره شد ✓',
      apiInvalid: 'آدرس نامعتبر است (باید با http:// یا https:// شروع شود).',
      langTitle: 'زبان رابط',
      langHint: 'تغییر زبان، جهت صفحه (RTL/LTR) و همهٔ متن‌ها را فوراً عوض می‌کند.',
      dataTitle: 'داده‌های محلی',
      dataHint: 'پاک‌کردن کلید کاربر، نام نمایشی و تنظیمات ذخیره‌شده روی این مرورگر.',
      dataButton: 'پاک‌کردن داده‌های محلی',
      dataDone: 'پاک شد — صفحه رفرش می‌شود…',
      endpointsTitle: 'نقاط اتصال داشبورد',
      endpoints: [
        { method: 'GET', path: '/api/v1/hub/runs?user_key=', desc: 'فهرست اجراهای من' },
        { method: 'POST', path: '/api/v1/hub/runs', desc: 'ثبت اجرای مدل در مرکز تجمیع' },
        { method: 'POST', path: '/api/v1/hub/runs/{id}/share', desc: 'اشتراک عمومی خروجی' },
        { method: 'GET', path: '/api/v1/hub/shared', desc: 'خروجی‌های به‌اشتراک‌گذاشته‌شده' },
      ],
    },
  },
  en: {
    profile: {
      kicker: 'Account',
      title: 'Profile',
      lead: 'Your HyDroMa dashboard identity — local-only, never sent to a server.',
      clientKeyTitle: 'Client key (anonymous)',
      clientKeyHint: 'This key is your identity in the data hub; model runs are stored under it. Do not share it.',
      copy: 'Copy',
      copied: 'Copied ✓',
      displayNameTitle: 'Display name',
      displayNameLabel: 'Your display name',
      displayNameHint: 'Stored only on this device.',
      save: 'Save',
      saved: 'Saved ✓',
      runsTitle: 'My registered runs',
      privacyNote: 'Per the privacy policy: no IP, no trackers, no personal data sent.',
    },
    settings: {
      kicker: 'Settings',
      title: 'Platform settings',
      lead: 'Local dashboard configuration — gateway URL, language and local data.',
      apiTitle: 'API gateway URL',
      apiHint: 'Default: http://localhost:8000 — change it to point at another server (applies immediately).',
      apiLabel: 'Gateway URL',
      apiSave: 'Save URL',
      apiSaved: 'Saved ✓',
      apiInvalid: 'Invalid URL (must start with http:// or https://).',
      langTitle: 'Interface language',
      langHint: 'Switching the language flips direction (RTL/LTR) and every text instantly.',
      dataTitle: 'Local data',
      dataHint: 'Clear the client key, display name and settings stored in this browser.',
      dataButton: 'Clear local data',
      dataDone: 'Cleared — reloading…',
      endpointsTitle: 'Dashboard endpoints',
      endpoints: [
        { method: 'GET', path: '/api/v1/hub/runs?user_key=', desc: 'List my runs' },
        { method: 'POST', path: '/api/v1/hub/runs', desc: 'Register a model run in the hub' },
        { method: 'POST', path: '/api/v1/hub/runs/{id}/share', desc: 'Share an output publicly' },
        { method: 'GET', path: '/api/v1/hub/shared', desc: 'Publicly shared outputs' },
      ],
    },
  },
} satisfies Record<'fa' | 'en', { profile: import('./profiletypes').ProfileContent; settings: import('./profiletypes').SettingsContent }>;
