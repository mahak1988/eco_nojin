import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { X, MessageSquare } from 'lucide-react';

/** Floating feedback widget (small button that expands). */
export default function FeedbackBubble() {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="fixed bottom-20 right-6 z-40 inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-4 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] shadow-lg shadow-leaf-900/40 hover:scale-105 transition-transform"
          aria-label={lang === 'fa' ? 'ارسال نظر' : 'Send feedback'}
        >
          <MessageSquare className="h-4 w-4" aria-hidden />
          {lang === 'fa' ? 'نظر بدهید' : 'Feedback'}
        </button>
      )}

      {open && (
        <div className="fixed bottom-20 right-6 z-40 w-80">
          <div className="glass rounded-3xl p-5 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold text-[var(--color-night-100)]">
                {lang === 'fa' ? 'نظر سريع' : 'Quick Feedback'}
              </span>
              <button type="button" onClick={() => setOpen(false)} className="text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]">
                <X className="h-4 w-4" aria-hidden />
              </button>
            </div>
            <p className="text-xs text-[var(--color-night-200)]/60">
              {lang === 'fa' ? 'چطور می‌توانیم بهبود بخشیم؟' : 'How can we improve?'}
            </p>
            <div className="mt-3 flex gap-2">
              {['😍', '😊', '😐', '😕', '😠'].map((emoji, i) => (
                <button key={i} type="button" className="text-xl hover:scale-125 transition-transform">{emoji}</button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
