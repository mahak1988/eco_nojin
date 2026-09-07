import { useEffect } from 'react';

/** Sets a per-route document title (SEO + tab label). */
export function usePageTitle(title: string): void {
  useEffect(() => {
    const prev = document.title;
    document.title = title;
    return () => {
      document.title = prev;
    };
  }, [title]);
}
