/** Status page content — the UI polls the real gateway /health endpoint. */

export interface StatusContent {
  kicker: string;
  title: string;
  lead: string;
  online: string;
  offline: string;
  checking: string;
  latencyLabel: string;
  refresh: string;
  autoNote: string;
  scopeTitle: string;
  scope: string[];
  incidentsTitle: string;
  incidentsNote: string;
}

export const status = {
  fa: {
    kicker: 'وضعیت سرویس',
    title: 'وضعیت زندهٔ درگاه',
    lead: 'این صفحه هر ۳۰ ثانیه سلامت واقعی درگاه FastAPI را بررسی می‌کند — بدون کش، بدون نمایش ساختگی.',
    online: 'درگاه فعال است',
    offline: 'درگاه پاسخ نمی‌دهد',
    checking: 'در حال بررسی…',
    latencyLabel: 'زمان پاسخ',
    refresh: 'بررسی دوباره',
    autoNote: 'بررسی خودکار هر ۳۰ ثانیه انجام می‌شود.',
    scopeTitle: 'چه چیزی بررسی می‌شود؟',
    scope: [
      'دسترس‌پذیری درگاه API و پاسخ endpoint سلامت (/health).',
      'زمان پاسخ به‌عنوان شاخص بار سرویس.',
      'وضعیت ۳۸ میکروسرویس داخلی با انتشار عمومی پلتفرم به همین صفحه اضافه می‌شود.',
    ],
    incidentsTitle: 'تاریخچهٔ رخدادها',
    incidentsNote: 'پس از انتشار عمومی، رخدادها و نگهداشت‌های برنامه‌ریزی‌شده در همین صفحه ثبت می‌شوند.',
  },
  en: {
    kicker: 'Service status',
    title: 'Live gateway status',
    lead: 'This page probes the real FastAPI gateway /health endpoint every 30 seconds — no caching, no fake indicators.',
    online: 'Gateway is online',
    offline: 'Gateway is not responding',
    checking: 'Checking…',
    latencyLabel: 'Response time',
    refresh: 'Check again',
    autoNote: 'Automatic check runs every 30 seconds.',
    scopeTitle: 'What is checked?',
    scope: [
      'API gateway reachability and the /health endpoint response.',
      'Response time as the service-load indicator.',
      'Per-service status of the 38 microservices is added to this page at public launch.',
    ],
    incidentsTitle: 'Incident history',
    incidentsNote: 'After public launch, incidents and scheduled maintenance are recorded on this page.',
  },
} satisfies Record<'fa' | 'en', StatusContent>;
