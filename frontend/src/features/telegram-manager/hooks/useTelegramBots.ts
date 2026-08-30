/**
 * useTelegramBots Hook
 * =====================
 * Manages Telegram bots state.
 *
 * Currently uses mock data. Ready for React Query integration:
 * - Replace useState with useQuery
 * - Add API endpoint in constants/config.ts
 *
 * @module features/telegram-manager/hooks
 */

import { useState, useCallback } from 'react';
import type { TelegramBot } from '../types';
import { MOCK_BOTS } from '../constants/mockBots';

interface UseTelegramBotsReturn {
  bots: TelegramBot[];
  toggleBot: (botId: string) => void;
  isLoading: boolean;
}

export function useTelegramBots(): UseTelegramBotsReturn {
  const [bots, setBots] = useState<TelegramBot[]>(MOCK_BOTS);

  const toggleBot = useCallback((botId: string) => {
    setBots((prev) =>
      prev.map((b) =>
        b.id === botId ? { ...b, active: !b.active } : b
      )
    );
  }, []);

  return {
    bots,
    toggleBot,
    isLoading: false, // Mock data loads instantly
  };
}
