/**
 * useClipboard Hook
 * ==================
 * Clipboard API wrapper with feedback state.
 *
 * @module features/crypto-payment/hooks
 */

import { useState, useCallback, useRef } from 'react';
import { CLIPBOARD_FEEDBACK_MS } from '../constants/config';

interface UseClipboardResult {
  copiedId: string | null;
  copy: (text: string, id: string) => Promise<void>;
}

export function useClipboard(): UseClipboardResult {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const copy = useCallback(async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        setCopiedId(null);
        timeoutRef.current = null;
      }, CLIPBOARD_FEEDBACK_MS);
    } catch (err) {
      console.error('Clipboard write failed:', err);
    }
  }, []);

  return { copiedId, copy };
}
