'use client';

import { useEffect } from 'react';
import { startWebVitalsReporting } from '@/lib/observability/web-vitals';

export function WebVitals() {
  useEffect(() => {
    startWebVitalsReporting();
  }, []);

  return null;
}
