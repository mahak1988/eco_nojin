"use client";

import React, { Component, ErrorInfo, ReactNode, type CSSProperties } from "react";
import { Button } from "./Button";

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  fallbackRender?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

const fallbackStyles: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "var(--space-8)",
  textAlign: "center",
  background: "var(--color-surface)",
  border: "1px solid var(--color-line)",
  borderRadius: "var(--radius-16)",
  gap: "var(--space-4)",
};

const iconStyles: CSSProperties = {
  fontSize: "3rem",
  lineHeight: 1,
};

const titleStyles: CSSProperties = {
  fontFamily: "var(--font-display)",
  fontSize: "1.5rem",
  fontWeight: 600,
  color: "var(--color-ink)",
  margin: 0,
};

const messageStyles: CSSProperties = {
  fontFamily: "var(--font-sans)",
  fontSize: "0.875rem",
  color: "var(--color-ink-soft)",
  margin: 0,
  maxWidth: "400px",
};

const detailsStyles: CSSProperties = {
  fontFamily: "var(--font-mono)",
  fontSize: "0.6875rem",
  color: "var(--color-ink-faint)",
  margin: 0,
  textAlign: "left",
  maxWidth: "500px",
  padding: "var(--space-3)",
  background: "var(--color-surface-2)",
  borderRadius: "var(--radius-8)",
  overflowX: "auto",
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ error, errorInfo });
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  reset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallbackRender) {
        return this.props.fallbackRender(this.state.error!, this.reset);
      }

      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={fallbackStyles} role="alert">
          <span style={iconStyles} aria-hidden="true">⚠️</span>
          <h2 style={titleStyles}>Something went wrong</h2>
          <p style={messageStyles}>
            We encountered an unexpected error. Please try again or contact support if the problem persists.
          </p>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <pre style={detailsStyles}>
              {this.state.error.message}
              {this.state.errorInfo?.componentStack && `\n\n${this.state.errorInfo.componentStack}`}
            </pre>
          )}
          <Button variant="primary" onClick={this.reset}>
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;