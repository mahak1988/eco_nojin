import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { Maximize2, X } from 'lucide-react';

/** Fullscreen project viewer modal. */
export default function FullscreenViewer({ projectName }: { projectName?: string }) {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-xl glass glass-hover px-4 py-2 text-xs font-bold text-[var(--color-night-100)] inline-flex items-center gap-2"
      >
        <Maximize2 className="h-4 w-4" aria-hidden />
        {lang === 'fa' ? 'نمایش کامل' : 'Fullscreen'}
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-[9998] bg-[var(--color-night-950)]/95 flex items-center justify-center p-8" onClick={() => setOpen(false)}>
      <div className="relative max-w-5xl w-full h-[80vh] rounded-3xl glass p-8 overflow-auto">
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="absolute top-4 left-4 text-[var(--color-night-200)]/40 hover:text-[var(--color-night-100)]"
        >
          <X className="h-6 w-6" aria-hidden />
        </button>
        <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] mb-4">
          {projectName || lang === 'fa' ? 'نمایش کامل پروژه' : 'Fullscreen Project'}
        </h2>
        <div className="grid grid-cols-2 gap-6">
          <div className="h-64 rounded-2xl bg-gradient-to-br from-[var(--color-night-800)] to-[var(--color-night-700)] flex items-center justify-center">
            <span className="text-6xl" aria-hidden>🛰️</span>
          </div>
          <div className="space-y-3">
            <div className="rounded-xl glass p-4">
              <p className="text-xs text-[var(--color-night-200)]/60">{lang === 'fa' ? 'مساحت' : 'Area'}</p>
              <p className="text-lg font-extrabold text-[var(--color-leaf-300)]">2,400 ha</p>
            </div>
            <div className="rounded-xl glass p-4">
              <p className="text-xs text-[var(--color-night-200)]/60">{lang === 'fa' ? 'پیشرفت' : 'Progress'}</p>
              <p className="text-lg font-extrabold text-[var(--color-leaf-300)]">72%</p>
            </div>
            <div className="rounded-xl glass p-4">
              <p className="text-xs text-[var(--color-night-200)]/60">{lang === 'fa' ? 'وضعیت' : 'Status'}</p>
              <p className="text-lg font-extrabold text-[var(--color-leaf-300)]">فعال</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
