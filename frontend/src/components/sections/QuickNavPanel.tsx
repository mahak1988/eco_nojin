import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { X, ArrowUpRight } from 'lucide-react';

/** Quick navigation panel. */
export default function QuickNavPanel() {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);

  const links = [
    { href: '/', label: 'خانه' },
    { href: '/platform', label: 'پلتفرم' },
    { href: '/dashboard', label: 'داشبورد' },
    { href: '/impact', label: 'تأثیر' },
    { href: '/blog', label: 'وبلاگ' },
    { href: '/contact', label: 'تماس' },
  ];

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded-xl glass p-2 text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]"
        aria-label={lang === 'fa' ? 'نواختن سریع' : 'Quick Nav'}
      >
        <ArrowUpRight className="h-5 w-5" aria-hidden />
      </button>
      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-56">
          <div className="rounded-2xl glass p-4 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-[var(--color-night-100)]">{lang === 'fa' ? 'پیمایش سریع' : 'Quick Nav'}</h3>
              <button type="button" onClick={() => setOpen(false)}>
                <X className="h-3 w-3 text-[var(--color-night-200)]/40" aria-hidden />
              </button>
            </div>
            <nav className="space-y-1">
              {links.map((link) => (
                <a key={link.href} href={link.href} className="block px-3 py-2 rounded-lg text-xs text-[var(--color-night-100)]/70 hover:bg-white/5 hover:text-[var(--color-leaf-300)]">
                  {lang === 'fa' ? link.label : link.label}
                </a>
              ))}
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
