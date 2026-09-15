import { useState } from 'react';
import { Bell, X, Check } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';

/** Central notification center. */
export default function NotificationCenter({
  max = 5,
}: {
  max?: number;
}) {
  const { lang } = useLang();
  const [notifications, setNotifications] = useState([
    { id: '1', text: 'پروژه جنگلشکاری به 72% رسید', read: false, time: '5m ago' },
    { id: '2', text: 'تأیید MRV جدید دریافت شد', read: false, time: '15m ago' },
    { id: '3', text: 'گزارش ماهانه آماده است', read: true, time: '2h ago' },
  ]);
  const [open, setOpen] = useState(false);

  const unread = notifications.filter((n) => !n.read).length;

  const markRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const dismiss = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="relative rounded-xl glass p-2 text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]"
        aria-label={lang === 'fa' ? 'اعلانات' : 'Notifications'}
      >
        <Bell className="h-5 w-5" aria-hidden />
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-[var(--color-leaf-500)] text-[8px] font-bold text-[var(--color-night-950)] flex items-center justify-center">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute top-full mt-2 left-0 w-80 z-50">
          <div className="rounded-2xl glass border border-white/10 overflow-hidden">
            <div className="flex items-center justify-between p-3 border-b border-white/5">
              <h3 className="text-sm font-bold text-[var(--color-night-100)]">
                {lang === 'fa' ? 'اعلانات' : 'Notifications'}
              </h3>
              <button
                type="button"
                onClick={() => setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))}
                className="text-[10px] text-[var(--color-leaf-300)]"
              >
                {lang === 'fa' ? 'همه خوانده' : 'Mark all read'}
              </button>
            </div>
            <div className="max-h-80 overflow-auto">
              {notifications.slice(0, max).map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-3 p-3 hover:bg-white/5 transition-colors ${!n.read ? 'bg-[var(--color-leaf-500)]/[0.03]' : ''}`}
                >
                  <div className="flex-1">
                    <p className={`text-xs ${!n.read ? 'font-bold text-[var(--color-night-100)]' : 'text-[var(--color-night-200)]/60'}`}>
                      {n.text}
                    </p>
                    <p className="text-[10px] text-[var(--color-night-200)]/40 mt-0.5">{n.time}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => markRead(n.id)}
                    className="text-[var(--color-night-200)]/30 hover:text-[var(--color-leaf-400)]"
                  >
                    <Check className="h-3 w-3" aria-hidden />
                  </button>
                  <button
                    type="button"
                    onClick={() => dismiss(n.id)}
                    className="text-[var(--color-night-200)]/30 hover:text-red-400"
                  >
                    <X className="h-3 w-3" aria-hidden />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
