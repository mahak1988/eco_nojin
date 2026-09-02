import { Component, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catches React errors (including WebGL context lost)
 * and shows a friendly fallback instead of crashing the app.
 */
export class SimulatorErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[Simulator] Crash caught by boundary:', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div style={{
          minHeight: '70vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
        }}>
          <Result
            status="error"
            title="شبیه‌ساز با خطا مواجه شد"
            subTitle={this.state.error?.message || 'WebGL context lost or rendering error'}
            extra={[
              <Button key="reset" type="primary" onClick={this.handleReset}>
                تلاش مجدد
              </Button>,
              <Button key="home" onClick={() => window.location.href = '/'}>
                بازگشت به صفحه اصلی
              </Button>,
            ]}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
