import { Link } from 'react-router-dom';
import { BookOpen, LifeBuoy, Mail, MessageCircleQuestion, ShieldCheck, TerminalSquare } from 'lucide-react';
import Seo from '../../../components/ui/Seo';
import { useLang } from '../../../i18n/LanguageContext';

/** B — dashboard support: gateway operations, access rules and where to get help. */
export default function DashboardSupportPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';

  const ops = [
    {
      title: isFa ? 'اجرای درگاه (بک‌اند)' : 'Start the gateway (backend)',
      code: 'cd D:\\eco_nojin\n.venv\\Scripts\\python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000',
    },
    {
      title: isFa ? 'اجرای فرانت‌اند (داشبورد)' : 'Start the frontend (dashboard)',
      code: 'cd D:\\eco_nojin\\frontend\npnpm dev',
    },
    {
      title: isFa ? 'آزمون سریع درگاه' : 'Quick gateway check',
      code: 'curl http://127.0.0.1:8000/health',
    },
  ];

  const rules = [
    {
      icon: ShieldCheck,
      title: isFa ? 'ورود (Bearer) برای POST' : 'Login (Bearer) for POST',
      body:
        isFa
          ? 'میان‌افزار CSRF درگاه، درخواست‌های POST را فقط با هدر Authorization: Bearer می‌پذیرد. از «ورود/ثبت‌نام» در سایدبار یک حساب بسازید تا همهٔ مدل‌ها اجرا شوند.'
          : 'The gateway CSRF middleware only accepts POSTs with an Authorization: Bearer header. Create an account via “Login / Register” in the sidebar to run models.',
    },
    {
      icon: TerminalSquare,
      title: isFa ? 'موتورهای ویژهٔ مدیر' : 'Admin-only motors',
      body:
        isFa
          ? 'موتورهای site-run (اقتصاد، AquaCrop، RothC، What-If، SWAT+، HEC-RAS) فقط برای نقش admin باز هستند. برای کاربران عادی، مسیر جایگزین «بهینه‌سازی زنجیرهٔ علمی» در صفحهٔ اقتصاد فعال است.'
          : 'site-run motors (economy, AquaCrop, RothC, What-If, SWAT+, HEC-RAS) are admin-only. Non-admin users can use the scientific-chain optimization fallback on the economy page.',
    },
    {
      icon: BookOpen,
      title: isFa ? 'اعتبارنامهٔ ماهواره (CDSE)' : 'Satellite credentials (CDSE)',
      body:
        isFa
          ? 'صحنهٔ واقعی NDVI فقط با اعتبارنامهٔ کوپرنیکوس در .env برگردانده می‌شود؛ بدون آن، صفحه به‌جای عدد ساختگی «در دسترس نیست» نشان می‌دهد.'
          : 'Real NDVI scenes require Copernicus credentials in .env; without them the page shows “unavailable” instead of a fabricated value.',
    },
  ];

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'پشتیبانی داشبورد' : 'Dashboard support'} | ${t.brand.name}`} path="/dashboard/support" />
      <h1 className="flex items-center gap-2 text-2xl font-extrabold text-ink-1">
        <LifeBuoy className="h-6 w-6 text-leaf-400" aria-hidden />
        {isFa ? 'پشتیبانی داشبورد' : 'Dashboard support'}
      </h1>

      <section className="glass rounded-[21px] p-5">
        <h2 className="mb-3 text-sm font-extrabold text-ink-1">{isFa ? 'دستورهای عملیاتی' : 'Operational commands'}</h2>
        <div className="flex flex-col gap-3">
          {ops.map((op) => (
            <div key={op.title}>
              <p className="mb-1 text-[11px] font-bold text-ink-3">{op.title}</p>
              <pre dir="ltr" className="overflow-x-auto rounded-xl bg-black/40 p-3 text-[11px] leading-6 text-aqua-300">
                <code>{op.code}</code>
              </pre>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rules.map((rule) => (
          <div key={rule.title} className="glass rounded-[21px] p-5">
            <rule.icon className="h-5 w-5 text-leaf-400" aria-hidden />
            <h3 className="mt-2 text-sm font-extrabold text-ink-1">{rule.title}</h3>
            <p className="mt-1.5 text-[11px] leading-6 text-ink-3">{rule.body}</p>
          </div>
        ))}
      </section>

      <section className="glass rounded-[21px] p-5">
        <h2 className="mb-3 text-sm font-extrabold text-ink-1">{isFa ? 'کانال‌های کمک' : 'Help channels'}</h2>
        <div className="flex flex-wrap gap-2 text-xs font-bold">
          <Link to="/support" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-ink-2">
            <MessageCircleQuestion className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'راهنمای کانال‌ها (USSD/SMS/صوت)' : 'Channel guides (USSD/SMS/Voice)'}
          </Link>
          <Link to="/faq" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-ink-2">
            {isFa ? 'پرسش‌های متداول' : 'FAQ'}
          </Link>
          <Link to="/dashboard/live/status" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-ink-2">
            {isFa ? 'وضعیت زندهٔ سرویس' : 'Live service status'}
          </Link>
          <Link to="/contact" className="glass glass-hover inline-flex items-center gap-2 rounded-full px-4 py-2 text-ink-2">
            <Mail className="h-4 w-4 text-leaf-400" aria-hidden />
            {isFa ? 'تماس با تیم' : 'Contact the team'}
          </Link>
        </div>
      </section>
    </div>
  );
}
