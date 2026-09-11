/** Developers page content (bilingual). Facts: gateway has 200+ documented
 * OpenAPI paths, JWT auth, active rate-limiting middleware. */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export interface CodeSample {
  label: string;
  code: string;
}

export interface DevelopersContent {
  kicker: string;
  title: string;
  lead: string;
  docsTitle: string;
  docsBody: string;
  docsButton: string;
  authTitle: string;
  authBody: string[];
  rateTitle: string;
  rateBody: string;
  samplesTitle: string;
  samples: CodeSample[];
}

export const developers = {
  fa: {
    kicker: 'برای توسعه‌دهندگان',
    title: 'درگاه API اکو نوژین',
    lead: 'همهٔ سرویس‌ها — از خاک و آب تا کربن و بازار — از یک درگاه FastAPI با مستندات تعاملی در دسترس‌اند.',
    docsTitle: 'مستندات تعاملی (Swagger)',
    docsBody:
      'درگاه در حال اجرا، مستندات تعاملی کامل (OpenAPI/Swagger) را روی مسیر /docs سرو می‌کند؛ بیش از ۲۰۰ مسیر مستند‌شده با امکان تست مستقیم از مرورگر.',
    docsButton: 'باز کردن Swagger',
    authTitle: 'احراز هویت',
    authBody: [
      'احراز هویت با توکن JWT است؛ توکن را از endpoint ورود بگیرید و در هدر Authorization با الگوی Bearer بفرستید.',
      'endpointهای عمومی (مثل سلامت سرویس و فرم تماس) بدون توکن هم پاسخ می‌دهند.',
    ],
    rateTitle: 'محدودسازی نرخ',
    rateBody:
      'درگاه به‌صورت سراسری محدودیت نرخ دارد تا سرویس برای همه پایدار بماند. برای سقف بالاتر (شرکا و یکپارچه‌سازان) از صفحهٔ تماس درخواست دهید.',
    samplesTitle: 'نمونه‌کدها',
    samples: [
      {
        label: 'cURL — سلامت سرویس',
        code: `curl ${API_BASE}/health`,
      },
      {
        label: 'cURL — ارسال پیام تماس',
        code: `curl -X POST ${API_BASE}/api/v1/contact \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Ali","email":"ali@example.com","message":"We want to join the pilot."}'`,
      },
      {
        label: 'Python — درخواست با توکن',
        code: `import requests

r = requests.get(
    "${API_BASE}/api/v1/soil/profiles",
    headers={"Authorization": "Bearer <TOKEN>"},
)
print(r.json())`,
      },
    ],
  },
  en: {
    kicker: 'For developers',
    title: 'The Eco Nojin API gateway',
    lead: 'Every service — from soil and water to carbon and marketplace — is reachable through one FastAPI gateway with interactive docs.',
    docsTitle: 'Interactive docs (Swagger)',
    docsBody:
      'A running gateway serves full OpenAPI/Swagger docs at /docs; 200+ documented paths, testable directly from the browser.',
    docsButton: 'Open Swagger',
    authTitle: 'Authentication',
    authBody: [
      'Authentication is JWT-based: obtain a token from the login endpoint and send it in the Authorization header as a Bearer token.',
      'Public endpoints (service health, the contact form) answer without a token.',
    ],
    rateTitle: 'Rate limiting',
    rateBody:
      'The gateway applies gateway-wide rate limiting so the service stays stable for everyone. For higher quotas (partners and integrators), request it via the contact page.',
    samplesTitle: 'Code samples',
    samples: [
      {
        label: 'cURL — service health',
        code: `curl ${API_BASE}/health`,
      },
      {
        label: 'cURL — submit a contact message',
        code: `curl -X POST ${API_BASE}/api/v1/contact \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Ali","email":"ali@example.com","message":"We want to join the pilot."}'`,
      },
      {
        label: 'Python — authenticated request',
        code: `import requests

r = requests.get(
    "${API_BASE}/api/v1/soil/profiles",
    headers={"Authorization": "Bearer <TOKEN>"},
)
print(r.json())`,
      },
    ],
  },
} satisfies Record<'fa' | 'en', DevelopersContent>;
