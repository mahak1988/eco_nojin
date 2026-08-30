/**
 * CryptoErrorBoundary
 * ====================
 * Catches errors in crypto payment widget to prevent full page crash.
 *
 * @module features/crypto-payment/components
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class CryptoErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[CryptoPaymentWidget] Error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          style={{
            padding: '40px',
            textAlign: 'center',
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: '12px',
            border: '1px solid rgba(239, 68, 68, 0.3)',
          }}
        >
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#ef4444', marginBottom: '8px' }}>
            خطا در بارگذاری ویجت پرداخت
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            {this.state.error?.message || 'خطای ناشناخته'}
          </div>
          <button
            onClick={this.handleRetry}
            className="btn-primary"
            style={{ padding: '8px 20px' }}
          >
            تلاش مجدد
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
