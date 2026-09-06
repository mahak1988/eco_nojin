import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Alert, Button } from '@eco/ui';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class GlobalErrorBoundary extends Component<Props, State> {
  override state: State = {
    hasError: false,
    error: null,
  };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // In production: ship to Sentry / observability backend
    if (typeof console !== 'undefined') {
      console.error('[GlobalErrorBoundary]', error, errorInfo);
    }
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  override render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex min-h-screen items-center justify-center bg-surface p-4">
          <Alert tone="danger" variant="outline" title="Unexpected application error">
            <p className="mb-3 text-sm">
              The dashboard caught an unrecoverable error. Reload the page or reset the boundary.
            </p>
            <pre className="mb-3 max-h-40 overflow-auto rounded bg-surface-muted p-2 text-[11px] text-ink">
              {this.state.error?.message ?? 'Unknown error'}
              {'\n'}
              {this.state.error?.stack?.split('\n').slice(0, 5).join('\n')}
            </pre>
            <div className="flex gap-2">
              <Button size="sm" onClick={this.handleReset}>
                Reset
              </Button>
              <Button size="sm" variant="outline" onClick={() => window.location.reload()}>
                Reload page
              </Button>
            </div>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}