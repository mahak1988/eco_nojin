/**
 * usePerformance Hook
 * ====================
 * Monitors Core Web Vitals and performance metrics.
 *
 * Metrics tracked:
 * - LCP (Largest Contentful Paint)
 * - FID (First Input Delay)
 * - CLS (Cumulative Layout Shift)
 * - FCP (First Contentful Paint)
 * - TTFB (Time to First Byte)
 *
 * @module hooks/usePerformance
 */

import { useEffect } from 'react';

interface MetricEntry {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
}

/**
 * Log performance metrics to console (dev only)
 * In production, send to analytics service
 */
function logMetric(metric: MetricEntry): void {
  const colors = {
    good: '#0cce6b',
    'needs-improvement': '#ffa400',
    poor: '#fd4e5d',
  };

  console.log(
    `%c[Perf] ${metric.name}: ${metric.value.toFixed(2)}ms (${metric.rating})`,
    `color: ${colors[metric.rating]}; font-weight: bold;`
  );
}

export function usePerformance(): void {
  useEffect(() => {
    // Only in development or when explicitly enabled
    if (import.meta.env.DEV) {
      // Lazy load web-vitals (small library)
      import('web-vitals')
        .then(({ onCLS, onINP, onLCP, onFCP, onTTFB }) => {
          onCLS(logMetric as any);
          onINP(logMetric as any);
          onLCP(logMetric as any);
          onFCP(logMetric as any);
          onTTFB(logMetric as any);
        })
        .catch(() => {
          // web-vitals not available
        });
    }
  }, []);
}
