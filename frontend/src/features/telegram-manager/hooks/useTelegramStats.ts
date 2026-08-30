/**
 * useTelegramStats Hook
 * ======================
 * Computes derived statistics from bots (memoized).
 *
 * @module features/telegram-manager/hooks
 */

import { useMemo } from 'react';
import type { TelegramBot, TelegramStats } from '../types';

export function useTelegramStats(bots: TelegramBot[]): TelegramStats {
  return useMemo(() => {
    const totalBots = bots.length;
    const activeBots = bots.filter((b) => b.active).length;
    const totalUsers = bots.reduce((sum, b) => sum + b.totalUsers, 0);
    const totalMessages = bots.reduce((sum, b) => sum + b.totalMessages, 0);

    return {
      totalBots,
      activeBots,
      totalUsers,
      totalMessages,
    };
  }, [bots]);
}
