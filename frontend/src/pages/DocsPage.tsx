import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import { Link } from 'react-router-dom';

const CONTENT = {
  fa: {
    title: 'مرکز مستندات',
    kicker: 'مستندات',
    lead: 'هر آنچه برای شروع نیاز دارید: راهنمای پلتفرم، مستندات علمی و API.',
    groups: [
      { title: 'شروع سریع', items: [['ثبت‌نام و ساخت حساب', '/register'], ['سفر کشاورز گام‌به‌گام', '/case-studies'], ['راهنمای USSD برای مناطق کم‌اینترنت', '/ussd-guide'], ['راهنمای صوتی', '/voice-guide']] },
      { title: 'علم و موتورها', items: [['داشبورد علمی هیدروما', '/hydroma'], ['پلتفرم و معماری', '/platform'], ['مستندات دوزبانه مخزن (docs/fa، docs/en)', 'https://github.com/openclaw/openclaw']] },
      { title: 'توسعه‌دهندگان', items: [['API باز (Swagger UI)', 'http://localhost:8000/docs'], ['مرجع API (OpenAPI JSON)', 'http://localhost:8000/openapi.json'], ['مخزن کد و مشارکت', 'https://github.com/openclaw/openclaw']] },
    ],
  },
  en: {
    title: 'Documentation hub',
    kicker: 'Documentation',
    lead: 'Everything you need to get started: platform guides, scientific docs and the API.',
    groups: [
      { title: 'Quick start', items: [['Create your account', '/register'], ['The farmer journey, step by step', '/case-studies'], ['USSD guide for low-connectivity regions', '/ussd-guide'], ['Voice guide', '/voice-guide']] },
      { title: 'Science & engines', items: [['HyDroMa scientific dashboard', '/hydroma'], ['Platform & architecture', '/platform'], ['Bilingual repo docs (docs/fa, docs/en)', 'https://github.com/openclaw/openclaw']] },
      { title: 'Developers', items: [['Open API (Swagger UI)', 'http://localhost:8000/docs'], ['API reference (OpenAPI JSON)', 'http://localhost:8000/openapi.json'], ['Source code & contributing', 'https://github.com/openclaw/openclaw']] },
    ],
  },
} as const;

export default function DocsPage() {
  const { lang } = useLang();
  const c = CONTENT[lang as 'fa' | 'en'];
  return (
    <>
      <Seo title={`${c.title} | Eco Nojin`} description={c.lead} path="/docs" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-3">
          {c.groups.map((g, i) => (
            <Reveal key={g.title} delay={i * 0.07}>
              <div className="glass h-full rounded-3xl p-7">
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{g.title}</h3>
                <ul className="mt-3 flex flex-col gap-2">
                  {g.items.map(([label, to]) => (
                    <li key={label}>
                      {to.startsWith('http')
                        ? <a href={to} target="_blank" rel="noreferrer" className="text-sm text-[var(--color-leaf-300)] hover:underline">{label} ↗</a>
                        : <Link to={to} className="text-sm text-[var(--color-leaf-300)] hover:underline">{label}</Link>}
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
