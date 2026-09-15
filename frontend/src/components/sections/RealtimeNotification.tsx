import { useEffect, useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { X, Bell } from 'lucide-react';

/** Live notification toast. */
export default function RealtimeNotification({
  message,
  duration = 5000,
}: {
  message?: string;
  duration?: number;
}) {
  const { lang } = useLang();
  const [visible, setVisible] = useState(false);
  const defaultMsg = lang === 'fa' ? '🔔 آخرین بروزرسانی پروژه منتشر شد' : '🔔 New project update published';

  useEffect(() => {
    const showTimer = setTimeout(() => setVisible(true), 3000);
    const hideTimer = setTimeout(() => setVisible(false), duration);
    return () => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
    };
  }, [duration]);

  if (!visible) return null;

  return (
    <div className="fixed top-6 left-6 z-50 max-w-sm animate-in fade-in slide-in-from-left-4">
      <div className="rounded-2xl glass border border-[var(--color-leaf-500)]/20 p-4 flex items-start gap-3">
        <Bell className="h-5 w-5 text-[var(--color-leaf-400)] mt-0.5 shrink-0" aria-hidden />
        <p className="text-sm text-[var(--color-night-100)] flex-1">{message || defaultMsg}</p>
        <button type="button" onClick={() => setVisible(false)} className="text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]">
          <X className="h-4 w-4" aria-hidden />
        </button>
      </div>
    </div>
  );
}
