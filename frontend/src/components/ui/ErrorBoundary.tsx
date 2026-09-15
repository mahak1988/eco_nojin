'use client';

import { Component, type ReactNode } from 'react';

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }
  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div role="alert" className="p-6 text-center" style={{ background: 'var(--color-night-950)', color: 'var(--color-night-100)', minHeight: '50vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.75rem' }}>خطا در بارگذاری بخش</h2>
            <p style={{ color: 'var(--color-night-200)', marginBottom: '1.5rem' }}>{this.state.error?.message ?? 'خطای ناشناخته'}</p>
            <button
              onClick={() => window.location.reload()}
              style={{ background: 'var(--color-leaf-500)', color: 'var(--color-night-950)', border: 'none', padding: '0.75rem 1.5rem', borderRadius: '9999px', fontWeight: 800, cursor: 'pointer' }}
            >
              بازنشانی صفحه
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
