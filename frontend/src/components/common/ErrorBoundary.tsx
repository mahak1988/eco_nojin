/**
 * ErrorBoundary - Catches React rendering errors gracefully
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          style={{
            padding: '40px 20px',
            textAlign: 'center',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            margin: '20px',
          }}
        >
          <div style={{ fontSize: '64px', marginBottom: '20px' }}>⚠️</div>
          <h2
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: 'var(--accent-danger)',
              marginBottom: '12px',
            }}
          >
            Component Error
          </h2>
          <p
            style={{
              fontSize: '14px',
              color: 'var(--text-muted)',
              marginBottom: '20px',
              maxWidth: '600px',
              margin: '0 auto 20px',
            }}
          >
            This component encountered an error and couldn't render properly.
          </p>

          <details
            style={{
              textAlign: 'left',
              maxWidth: '800px',
              margin: '0 auto',
              background: 'var(--bg-secondary)',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
            }}
          >
            <summary
              style={{
                cursor: 'pointer',
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: '12px',
              }}
            >
              Error Details
            </summary>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              <p style={{ fontWeight: 600, marginBottom: '8px' }}>Error:</p>
              <pre
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  padding: '12px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  marginBottom: '12px',
                }}
              >
                {this.state.error?.toString()}
              </pre>

              <p style={{ fontWeight: 600, marginBottom: '8px' }}>Stack:</p>
              <pre
                style={{
                  background: 'var(--bg-hover)',
                  padding: '12px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '11px',
                  lineHeight: '1.5',
                }}
              >
                {this.state.errorInfo?.componentStack}
              </pre>
            </div>
          </details>

          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '24px',
              padding: '12px 24px',
              background: 'linear-gradient(135deg, var(--accent-primary) 0%, #059669 100%)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
