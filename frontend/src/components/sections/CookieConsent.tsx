import { useState, useEffect } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { Cookie, X, CheckCircle2 } from 'lucide-react';

/** Cookie consent banner. */
export default function CookieConsent() {
  const { lang } = useLang();
  const [visible, setVisible] = useState(false);
  const [accepted, setAccepted] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem('cookie_consent', 'accepted');
    setAccepted(true);
  };

  const dismiss = () => {
    localStorage.setItem('cookie_consent', 'dismissed');
    setVisible(false);
  };

  if (!visible || accepted) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50">
      <div className="mx-auto max-w-6xl p-4">
        <div className="glass rounded-2xl border border-white/10 p-5 flex flex-col items-center gap-4">
          <div className="flex items-center gap-3">
            <Cookie className="h-5 w-5 text-[var(--color-sand-400)]" aria-hidden />
            <p className="text-sm text-[var(--color-night-100)]">
              {lang === 'fa'
                ? 'ما از کوکی‌ها برای بهبود تجربه شما استفاده می‌کنیم.'
                : 'We use cookies to improve your experience.'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={accept}
              className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-leaf-500)] px-5 py-2 text-xs font-extrabold text-[var(--color-night-950)] hover:scale-[1.03] transition-transform"
            >
              <CheckCircle2 className="h-3 w-3" aria-hidden />
              {lang === 'fa' ? 'پذیرش' : 'Accept'}
            </button>
            <button
              type="button"
              onClick={dismiss}
              className="rounded-full glass px-5 py-2 text-xs font-bold text-[var(--color-night-200)] hover:text-[var(--color-night-100)] transition-colors"
            >
              <X className="inline h-3 w-3 mr-1" aria-hidden />
              {lang === 'fa' ? 'رد' : 'Decline'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
