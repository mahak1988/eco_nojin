/** Toast notification system — vanilla React, no external deps. */

import { createContext, useContext, useState, useCallback, useRef } from 'react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, 'id'>) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const showToast = useCallback(
    ({ type, title, description, duration = 4000 }: Omit<Toast, 'id'>) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      const toast: Toast = { id, type, title, description, duration };
      setToasts((prev) => [...prev, toast]);

      if (duration > 0) {
        const timer = setTimeout(() => dismissToast(id), duration);
        timers.current.set(id, timer);
      }

      return id;
    },
    [dismissToast],
  );

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" role="region" aria-live="polite">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const [isExiting, setIsExiting] = useState(false);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => onDismiss(toast.id), 200);
  };

  const colors = {
    success: 'border-[var(--color-leaf-500)]/40 bg-[var(--color-leaf-500)]/10 text-[var(--color-leaf-300)]',
    error: 'border-red-500/40 bg-red-500/10 text-red-300',
    warning: 'border-[var(--color-sand-500)]/40 bg-[var(--color-sand-500)]/10 text-[var(--color-sand-300)]',
    info: 'border-[var(--color-aqua-500)]/40 bg-[var(--color-aqua-500)]/10 text-[var(--color-aqua-300)]',
  };

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
  };

  return (
    <div
      className={`glass flex items-start gap-3 rounded-2xl border px-4 py-3 shadow-lg transition-all duration-200 ${
        isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'
      } ${colors[toast.type]}`}
      style={{ minWidth: '320px', maxWidth: '480px' }}
    >
      <span className="mt-0.5 text-sm font-extrabold">{icons[toast.type]}</span>
      <div className="flex-1">
        <p className="text-sm font-extrabold text-[var(--color-night-100)]">{toast.title}</p>
        {toast.description && <p className="mt-0.5 text-xs text-[var(--color-night-200)]/60">{toast.description}</p>}
      </div>
        <button
          type="button"
          onClick={handleDismiss}
          className="shrink-0 rounded-lg p-1 text-[var(--color-night-200)]/50 hover:text-[var(--color-night-100)]"
          aria-label="Dismiss"
        >
        ✕
      </button>
    </div>
  );
}
