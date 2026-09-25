'use client';

import { type ReactNode, useEffect } from 'react';
import { registerConnectivityListeners } from '@/lib/offline/connectivity';
import { flushOfflineOutbox } from '@/lib/offline/outbox';

export function OfflineProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const unregister = registerConnectivityListeners((online) => {
      if (online) void flushOfflineOutbox();
    });
    return unregister;
  }, []);

  return children;
}
