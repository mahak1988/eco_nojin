import { Component, type ReactNode } from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 px-4 text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)]">خطایی رخ داده است</h2>
          <p className="max-w-md text-sm leading-7 text-[var(--color-night-200)]/60">
            متأسفانه در بارگذاری این صفحه خطایی رخ داده است. لطفاً صفحه را.refresh کنید یا به صفحه اصلی برگردید.
          </p>
          <button
            type="button"
            onClick={() => {
              this.setState({ hasError: false, error: null });
            }}
            className="rounded-full bg-[var(--color-leaf-500)] px-6 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
          >
            تلاش مجدد
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
