'use client';

import { onCLS, onINP, onLCP } from 'web-vitals';

type VitalPayload = {
  name: string;
  value: number;
  id: string;
  navigationType: string;
};

function report(payload: VitalPayload): void {
  if (typeof navigator === 'undefined' || typeof navigator.sendBeacon !== 'function') return;
  navigator.sendBeacon(
    '/api/observability/web-vitals',
    new Blob([JSON.stringify(payload)], { type: 'application/json' }),
  );
}

export function startWebVitalsReporting(): void {
  onCLS(report);
  onINP(report);
  onLCP(report);
}
