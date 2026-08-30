/**
 * TerrainMesh Error Boundary
 * ===========================
 * Catches WebGL/Three.js errors to prevent full page crashes.
 *
 * When WebGL context is lost or shader compilation fails, this component
 * shows a fallback UI instead of crashing the entire page.
 *
 * @module features/hydroma/components/canvas/TerrainMeshErrorBoundary
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

// ─────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

// ─────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────

export class TerrainMeshErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[TerrainMeshErrorBoundary] Error caught:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <mesh>
          <planeGeometry args={[20, 20]} />
          <meshBasicMaterial color="#ef4444" opacity={0.5} transparent />
        </mesh>
      );
    }

    return this.props.children;
  }
}
