'use client';
import { useState, useEffect, ReactNode } from 'react';

interface ClientOnlyProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * ClientOnly component - renders ONLY after client-side hydration.
 *
 * This is the BULLETPROOF solution for hydration mismatches caused by:
 * - Browser APIs (navigator, window, localStorage)
 * - Date.now(), Math.random()
 * - User's locale/timezone
 *
 * Server: renders fallback (or nothing)
 * Client: renders children AFTER mount
 */
export default function ClientOnly({ children, fallback = null }: ClientOnlyProps) {
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
  }, []);

  if (!hasMounted) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
